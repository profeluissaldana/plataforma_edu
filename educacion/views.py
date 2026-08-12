import os
import socket
import subprocess
import sys
import time
from datetime import date, datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Avg, Count, Prefetch, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from usuarios.models import Asistencia
from .models import (
    Actividad,
    EntregaActividad,
    EspacioEducativo,
    Leccion,
    Modulo,
    Opcion,
    Pregunta,
    ProgresoTeoria,
    RegistroCicloLectivo,
    RespuestaUsuario,
)

Usuario = get_user_model()

# ==============================================================================
# HELPER: GESTIÓN DINÁMICA DE WEBSOCKIFY / VNC
# ==============================================================================
# Mapeo: { '192.168.1.50': {'puerto': 6081, 'proceso': <Popen>} }
VNC_PORT_MAPPING = {}
STARTING_PORT = 6081


def buscar_puerto_libre(puerto_inicial=STARTING_PORT):
    """Encuentra un puerto TCP libre en el servidor para lanzar websockify."""
    puerto = puerto_inicial
    while puerto < 65000:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', puerto)) != 0:
                return puerto
            puerto += 1
    raise RuntimeError("No hay puertos disponibles en el servidor")


def obtener_o_crear_puerto_vnc(ip_cliente):
    """Devuelve el puerto de Websockify asignado a la IP del alumno,
    iniciando el subproceso si aún no existe o liberando recursos si expiró.
    """
    global VNC_PORT_MAPPING

    # 1. Si la IP ya está registrada, verificar si el proceso y el socket siguen activos
    if ip_cliente in VNC_PORT_MAPPING:
        registro = VNC_PORT_MAPPING[ip_cliente]
        puerto_actual = registro['puerto']
        proceso_actual = registro.get('proceso')

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            if s.connect_ex(('127.0.0.1', puerto_actual)) == 0:
                return puerto_actual

        # Si el socket no respondió, terminar limpiamente el subproceso anterior
        if proceso_actual and proceso_actual.poll() is None:
            proceso_actual.terminate()
            try:
                proceso_actual.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proceso_actual.kill()

        del VNC_PORT_MAPPING[ip_cliente]

    # 2. Buscar un nuevo puerto disponible
    nuevo_puerto = buscar_puerto_libre()

    # 3. Resolver la ruta absoluta del directorio estático de noVNC
    if hasattr(settings, 'STATICFILES_DIRS') and settings.STATICFILES_DIRS:
        ruta_base_estat = settings.STATICFILES_DIRS[0]
    elif hasattr(settings, 'STATIC_ROOT') and settings.STATIC_ROOT:
        ruta_base_estat = settings.STATIC_ROOT
    else:
        ruta_base_estat = os.path.join(settings.BASE_DIR, 'static')

    ruta_novnc = os.path.join(ruta_base_estat, 'novnc')

    cmd = [
        sys.executable, "-m", "websockify",
        "--web", str(ruta_novnc),
        str(nuevo_puerto),
        f"{ip_cliente}:5900"
    ]

    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        raise RuntimeError(f"Error al iniciar subproceso websockify: {e}")

    # 4. Espera activa para asegurar que websockify haya abierto el puerto
    puerto_listo = False
    for _ in range(10):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            if s.connect_ex(('127.0.0.1', nuevo_puerto)) == 0:
                puerto_listo = True
                break
        time.sleep(0.1)

    if not puerto_listo:
        proc.terminate()
        raise RuntimeError(f"Websockify no logró abrir el puerto {nuevo_puerto} para la IP {ip_cliente}")

    VNC_PORT_MAPPING[ip_cliente] = {
        'puerto': nuevo_puerto,
        'proceso': proc
    }

    return nuevo_puerto


# ==============================================================================
# ENDPOINTS Y MAPEOS DE ASISTENCIA / IP
# ==============================================================================
@csrf_exempt
def reportar_ip_equipo(request):
    """
    Endpoint que reciben los clientes para registrar/actualizar su IP en la LAN.
    Se pasa 'equipo' (username) vía POST.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    equipo_username = request.POST.get('equipo')
    
    if not equipo_username:
        return JsonResponse({'error': 'Falta el parámetro equipo'}, status=400)

    ip_cliente = request.META.get('HTTP_X_FORWARDED_FOR')
    if ip_cliente:
        ip_cliente = ip_cliente.split(',')[0].strip()
    else:
        ip_cliente = request.META.get('REMOTE_ADDR')

    try:
        usuario_equipo = Usuario.objects.get(username=equipo_username)
        usuario_equipo.ip_local = ip_cliente
        usuario_equipo.save(update_fields=['ip_local'])
        return JsonResponse({
            'status': 'ok',
            'equipo': equipo_username,
            'ip_registrada': ip_cliente
        })
    except Usuario.DoesNotExist:
        return JsonResponse({'error': 'Equipo/Usuario no encontrado'}, status=404)


MAPA_TURNOS = {
    'TARDE': 'T',
    'Tarde': 'T',
    'tarde': 'T',
    'T': 'T',
    'MAÑANA': 'M',
    'Mañana': 'M',
    'mañana': 'M',
    'M': 'M',
}


# ==============================================================================
# HELPER: CÁLCULO DE PROGRESO Y ACTIVIDADES COMPLETADAS
# ==============================================================================
def obtener_progreso_estudiante(estudiante, espacio):
    """Calcula el porcentaje global de avance del alumno en un Espacio Educativo
    y devuelve la lista de IDs de actividades completadas.
    """
    if not estudiante.is_authenticated:
        return 0, set()

    filtro_espacio_actividades = Q(
        leccion__modulo__espacio_educativo=espacio
    ) | Q(subleccion__leccion__modulo__espacio_educativo=espacio)

    total_actividades = Actividad.objects.filter(
        filtro_espacio_actividades, activo=True
    ).count()

    if total_actividades == 0:
        return 0, set()

    filtro_espacio_relacionado = Q(
        actividad__leccion__modulo__espacio_educativo=espacio
    ) | Q(actividad__subleccion__leccion__modulo__espacio_educativo=espacio)

    entregas_completas = EntregaActividad.objects.filter(
        filtro_espacio_relacionado,
        estudiante=estudiante,
        estado__in=['ENVIADO', 'CALIFICADO'],
    ).values_list('actividad_id', flat=True).distinct()

    teorias_completas = ProgresoTeoria.objects.filter(
        filtro_espacio_relacionado,
        estudiante=estudiante,
        completado=True,
    ).values_list('actividad_id', flat=True).distinct()

    actividades_resueltas_ids = set(entregas_completas) | set(teorias_completas)

    porcentaje = round(
        (len(actividades_resueltas_ids) / total_actividades) * 100
    )
    return porcentaje, actividades_resueltas_ids


# ==============================================================================
# VISTAS PRINCIPALES Y CONTROL REMOTO
# ==============================================================================
@login_required
def inicio(request):
    """Vista principal que lista los Espacios Educativos activos."""
    espacios = EspacioEducativo.objects.filter(activo=True)
    return render(request, 'educacion/inicio.html', {'espacios': espacios})


@login_required
def ver_pantalla_alumno(request, alumno_id):
    """Vista para abrir la transmisión VNC/noVNC en tiempo real del alumno."""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'No tienes permisos para realizar monitoreo remoto.')
        return redirect('educacion:inicio')

    alumno = get_object_or_404(Usuario, pk=alumno_id)

    if not getattr(alumno, 'ip_local', None):
        messages.error(request, f'El equipo {alumno.username} no ha reportado su IP local aún.')
        return redirect('educacion:ver_grupos')

    try:
        puerto_vnc = obtener_o_crear_puerto_vnc(alumno.ip_local)
    except Exception as e:
        messages.error(request, f'Error al iniciar el túnel de monitoreo: {e}')
        return redirect('educacion:ver_grupos')

    host_servidor = request.get_host().split(':')[0]

    contexto = {
        'alumno': alumno,
        'puerto_vnc': puerto_vnc,
        'host_servidor': host_servidor,
    }
    return render(request, 'educacion/control_remoto.html', contexto)


@login_required
def detalle_espacio(request, espacio_id):
    """Vista responsiva que muestra el detalle de un Espacio Educativo."""
    espacio = get_object_or_404(EspacioEducativo, id=espacio_id, activo=True)

    if espacio.id == 4:
        contexto = {
            'espacio': espacio,
            'progreso_porcentaje': 0,
            'examen_desbloqueado': False,
            'clave_error': False,
            'estudiante': request.user,
        }

        if request.method == 'POST':
            clave_ingresada = request.POST.get('clave_acceso', '').strip()
            if clave_ingresada == 'GIT123':
                contexto['examen_desbloqueado'] = True
                messages.success(request, '¡Examen desbloqueado con éxito!')
            else:
                contexto['clave_error'] = True
                messages.error(
                    request, 'Clave incorrecta. Intenta nuevamente.'
                )

        return render(request, 'educacion/gitgithub.html', contexto)

    modulos = (
        espacio.modulos.filter(activo=True)
        .order_by('orden')
        .prefetch_related(
            Prefetch(
                'lecciones',
                queryset=Leccion.objects.filter(activo=True).order_by('orden'),
            ),
            'lecciones__contenidos',
            'lecciones__actividades',
            'lecciones__sublecciones',
            'lecciones__sublecciones__contenidos',
            'lecciones__sublecciones__actividades',
        )
    )

    porcentaje_avance, actividades_resueltas_ids = (
        obtener_progreso_estudiante(request.user, espacio)
    )

    return render(
        request,
        'educacion/detalle_espacio.html',
        {
            'espacio': espacio,
            'modulos': modulos,
            'porcentaje_avance': porcentaje_avance,
            'actividades_resueltas_ids': actividades_resueltas_ids,
            'estudiante': request.user,
        },
    )


@login_required
def html_css_modulo1_view(request):
    """Vista para renderizar el Módulo 1 de HTML y procesar su evaluación."""
    if request.method == 'POST' and 'btn_enviar_evaluacion' in request.POST:
        p1 = request.POST.get('p1')
        p2 = request.POST.get('p2')
        p3 = request.POST.get('p3')
        p4 = request.POST.get('p4')

        aciertos = 0
        if p1 == 'b': aciertos += 1
        if p2 == 'c': aciertos += 1
        if p3 == 'a': aciertos += 1
        if p4 == 'b': aciertos += 1

        porcentaje = round((aciertos / 4) * 100)

        if porcentaje >= 70:
            messages.success(
                request,
                f'¡Felicidades! Aprobaste el Módulo 1 con un {porcentaje}%'
                f' ({aciertos}/4 aciertos).',
            )
        else:
            messages.warning(
                request,
                f'Obtuviste un {porcentaje}% ({aciertos}/4 aciertos). Revisa'
                ' el contenido e intenta nuevamente.',
            )

        return redirect('educacion:html_css_modulo1')

    return render(request, 'educacion/htmlcss_modulo1.html')


@login_required
def git_github_view(request):
    """Vista directa para renderizar el módulo interactivo de Git y GitHub."""
    contexto = {
        'progreso_porcentaje': 0,
        'examen_desbloqueado': False,
        'clave_error': False,
        'estudiante': request.user,
    }

    if request.method == 'POST':
        clave_ingresada = request.POST.get('clave_acceso', '').strip()
        if clave_ingresada == 'GIT123':
            contexto['examen_desbloqueado'] = True
            messages.success(request, '¡Examen desbloqueado con éxito!')
        else:
            contexto['clave_error'] = True
            messages.error(request, 'Clave incorrecta. Intenta nuevamente.')

    return render(request, 'educacion/gitgithub.html', contexto)


@login_required
def marcar_teoria_completada(request, actividad_id):
    """Permite al alumno marcar una lectura o video como completado."""
    actividad = get_object_or_404(Actividad, id=actividad_id, activo=True)

    ProgresoTeoria.objects.get_or_create(
        estudiante=request.user,
        actividad=actividad,
        defaults={'completado': True},
    )

    messages.success(
        request, f'¡Excelente! Has completado: {actividad.titulo}'
    )

    if actividad.leccion:
        espacio_id = actividad.leccion.modulo.espacio_educativo.id
    elif actividad.subleccion:
        espacio_id = actividad.subleccion.leccion.modulo.espacio_educativo.id
    else:
        return redirect('educacion:inicio')

    return redirect('educacion:detalle_espacio', espacio_id=espacio_id)


@login_required
def realizar_actividad(request, actividad_id):
    """Vista polimórfica para entregas y cuestionarios."""
    actividad = get_object_or_404(
        Actividad.objects.prefetch_related(
            Prefetch(
                'preguntas',
                queryset=Pregunta.objects.filter(activo=True)
                .order_by('orden')
                .prefetch_related('opciones'),
            )
        ),
        id=actividad_id,
        activo=True,
    )

    entrega, _ = EntregaActividad.objects.get_or_create(
        actividad=actividad, estudiante=request.user
    )

    if entrega.estado in ['ENVIADO', 'CALIFICADO']:
        puntaje_obtenido = (
            entrega.calificacion or entrega.puntaje_obtenido or 0
        )
        puntaje_total = (
            sum(p.puntaje for p in actividad.preguntas.all()) or 1
        )
        porcentaje = (
            round((puntaje_obtenido / puntaje_total) * 100, 1)
            if actividad.preguntas.exists()
            else 100
        )

        return render(
            request,
            'educacion/realizar_actividad.html',
            {
                'actividad': actividad,
                'entrega': entrega,
                'ya_enviado': True,
                'puntaje_obtenido': puntaje_obtenido,
                'puntaje_total': puntaje_total,
                'porcentaje': porcentaje,
                'estudiante': request.user,
            },
        )

    if actividad.tipo == 'PRACTICA':
        if request.method == 'POST' and 'btn_subir_practica' in request.POST:
            archivo = request.FILES.get('archivo_adjunto')
            comentario = request.POST.get('comentario_estudiante', '').strip()

            if archivo:
                entrega.archivo_adjunto = archivo
                entrega.comentario_estudiante = comentario
                entrega.estado = 'ENVIADO'
                entrega.save()

                messages.success(
                    request, '¡Tu archivo de práctica ha sido subido con éxito!'
                )
                return redirect(
                    'educacion:realizar_actividad', actividad_id=actividad.id
                )
            else:
                messages.error(
                    request,
                    'Debes adjuntar un archivo para poder realizar la entrega.',
                )

        return render(
            request,
            'educacion/realizar_actividad.html',
            {
                'actividad': actividad,
                'entrega': entrega,
                'es_practica': True,
                'ya_enviado': False,
                'estudiante': request.user,
            },
        )

    session_key = f'actividad_clave_validada_{actividad.id}'
    tiene_clave = bool(
        actividad.clave_acceso and actividad.clave_acceso.strip()
    )
    clave_validada = request.session.get(session_key, False)

    if tiene_clave and not clave_validada:
        if request.method == 'POST' and 'btn_validar_clave' in request.POST:
            clave_ingresada = request.POST.get('clave_acceso', '').strip()
            if clave_ingresada == actividad.clave_acceso.strip():
                request.session[session_key] = True
                messages.success(
                    request, '¡Clave correcta! Puedes comenzar la evaluación.'
                )
                return redirect(
                    'educacion:realizar_actividad', actividad_id=actividad.id
                )
            else:
                messages.error(
                    request, 'La clave ingresada es incorrecta.'
                )

        return render(
            request,
            'educacion/realizar_actividad.html',
            {
                'actividad': actividad,
                'requiere_clave': True,
                'ya_enviado': False,
                'estudiante': request.user,
            },
        )

    if request.method == 'POST' and 'btn_enviar_respuestas' in request.POST:
        puntaje_total_obtenido = 0

        with transaction.atomic():
            for pregunta in actividad.preguntas.all():
                campo_name = f'pregunta_{pregunta.id}'

                if pregunta.tipo in ['OPCION_MULTIPLE', 'VERDADERO_FALSO']:
                    opcion_id = request.POST.get(campo_name)
                    if opcion_id:
                        opcion_obj = Opcion.objects.filter(
                            id=opcion_id, pregunta=pregunta
                        ).first()
                        RespuestaUsuario.objects.update_or_create(
                            entrega=entrega,
                            pregunta=pregunta,
                            defaults={'opcion_seleccionada': opcion_obj},
                        )
                        if opcion_obj and opcion_obj.es_correcta:
                            puntaje_total_obtenido += pregunta.puntaje

                elif pregunta.tipo in ['RESPUESTA_CORTA', 'RESPUESTA_LARGA']:
                    texto = request.POST.get(campo_name, '').strip()
                    if texto:
                        RespuestaUsuario.objects.update_or_create(
                            entrega=entrega,
                            pregunta=pregunta,
                            defaults={'texto_respuesta': texto},
                        )

            entrega.estado = 'ENVIADO'
            entrega.calificacion = puntaje_total_obtenido
            entrega.puntaje_obtenido = puntaje_total_obtenido
            entrega.save()

        if session_key in request.session:
            del request.session[session_key]

        messages.success(
            request,
            '¡Tus respuestas han sido guardadas y enviadas correctamente!',
        )
        return redirect(
            'educacion:realizar_actividad', actividad_id=actividad.id
        )

    respuestas_existentes = {
        resp.pregunta_id: resp
        for resp in RespuestaUsuario.objects.filter(entrega=entrega)
    }

    return render(
        request,
        'educacion/realizar_actividad.html',
        {
            'actividad': actividad,
            'entrega': entrega,
            'respuestas_existentes': respuestas_existentes,
            'requiere_clave': False,
            'ya_enviado': False,
            'estudiante': request.user,
        },
    )


# ==============================================================================
# VISTAS DEL PANEL DE GESTIÓN PEDAGÓGICA Y ASISTENCIA
# ==============================================================================
@login_required
def tomar_asistencia_jornada(request):
    """Permite al docente registrar o actualizar la asistencia del día."""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('educacion:inicio')

    curso_filtro = request.GET.get('curso', '')
    turno_filtro = request.GET.get('turno', '')
    dia_filtro = request.GET.get('dia_cursado', '')
    
    fecha_input = request.GET.get('fecha')
    try:
        fecha_obj = (
            datetime.strptime(fecha_input, '%Y-%m-%d').date()
            if fecha_input
            else date.today()
        )
    except ValueError:
        fecha_obj = date.today()

    fecha_str = str(fecha_obj)

    alumnos = Usuario.objects.filter(is_superuser=False, is_staff=False)

    if curso_filtro:
        alumnos = alumnos.filter(curso=curso_filtro)
    if turno_filtro:
        turno_codigo = MAPA_TURNOS.get(turno_filtro, turno_filtro)
        alumnos = alumnos.filter(turno=turno_codigo)
    if dia_filtro:
        alumnos = alumnos.filter(dia_cursado__icontains=dia_filtro)

    alumnos = alumnos.order_by('last_name', 'first_name')

    if request.method == 'POST':
        fecha_asistencia_input = request.POST.get('fecha', str(date.today()))
        try:
            fecha_asistencia = datetime.strptime(fecha_asistencia_input, '%Y-%m-%d').date()
        except ValueError:
            fecha_asistencia = date.today()

        with transaction.atomic():
            for alumno in alumnos:
                estado = request.POST.get(f'asistencia_{alumno.id}', 'AUSENTE')
                observacion = request.POST.get(f'obs_{alumno.id}', '').strip()

                Asistencia.objects.update_or_create(
                    alumno=alumno,
                    fecha=fecha_asistencia,
                    defaults={
                        'estado': estado,
                        'observacion': observacion,
                    },
                )

        messages.success(request, f'Asistencia del {fecha_asistencia} registrada con éxito.')
        url = f"{reverse('educacion:tomar_asistencia_jornada')}?curso={curso_filtro}&turno={turno_filtro}&dia_cursado={dia_filtro}&fecha={fecha_asistencia}"
        return redirect(url)

    asistencias_hoy = {
        a.alumno_id: a
        for a in Asistencia.objects.filter(fecha=fecha_str, alumno__in=alumnos)
    }

    alumnos_con_asistencia = [
        {
            'alumno': alumno,
            'estado': asistencias_hoy[alumno.id].estado if alumno.id in asistencias_hoy else 'PRESENTE',
            'observaciones': asistencias_hoy[alumno.id].observacion if alumno.id in asistencias_hoy else '',
        }
        for alumno in alumnos
    ]

    contexto = {
        'alumnos_con_asistencia': alumnos_con_asistencia,
        'fecha': fecha_str,
        'curso_filtro': curso_filtro,
        'turno_filtro': turno_filtro,
        'dia_filtro': dia_filtro,
    }
    return render(request, 'asistencias/tomar_asistencia.html', contexto)


@login_required
def ver_grupos(request):
    """Muestra el listado de alumnos agrupados por curso, turno y día de cursado."""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('educacion:inicio')

    alumnos = Usuario.objects.filter(
        is_superuser=False, is_staff=False
    ).order_by('curso', 'turno', 'last_name', 'first_name')

    grupos = {}
    for alumno in alumnos:
        clave_grupo = f"{alumno.curso or 'Sin Curso'} - Turno: {alumno.turno or 'N/D'} ({alumno.dia_cursado or 'Sin día'})"
        if clave_grupo not in grupos:
            grupos[clave_grupo] = []
        grupos[clave_grupo].append(alumno)

    return render(request, 'educacion/ver_grupos.html', {'grupos': grupos})


@login_required
def historial_asistencias(request):
    """Muestra el historial completo de asistencias registradas."""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('educacion:inicio')

    asistencias = Asistencia.objects.select_related('alumno').order_by('-fecha', 'alumno__last_name')
    return render(request, 'asistencias/historial_asistencias.html', {'asistencias': asistencias})


@login_required
def reiniciar_ciclo_lectivo(request):
    """Reinicia el ciclo lectivo registrando el evento y eliminando cuentas de alumnos."""
    if not request.user.is_superuser:
        messages.error(request, 'No tienes permisos para realizar esta acción.')
        return redirect('educacion:inicio')

    if request.method == 'POST':
        with transaction.atomic():
            alumnos_qs = Usuario.objects.filter(is_superuser=False, is_staff=False)
            cantidad_eliminados = alumnos_qs.count()

            RegistroCicloLectivo.objects.create(
                anio=date.today().year,
                alumnos_eliminados=cantidad_eliminados,
                realizado_por=request.user,
            )

            alumnos_qs.delete()

            messages.success(
                request,
                f'Ciclo lectivo reiniciado correctamente. Se procesaron {cantidad_eliminados} alumnos.',
            )
            return redirect('educacion:inicio')

    return render(request, 'educacion/confirmar_reinicio_ciclo.html')


@login_required
def panel_avance_alumnos(request):
    """Calcula el porcentaje de asistencia, porcentaje global de avance 
    en actividades y desglosa las notas obtenidas por alumno (optimizado contra N+1).
    """
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('educacion:inicio')

    curso_filtro = request.GET.get('curso', '')
    
    alumnos_qs = Usuario.objects.filter(is_superuser=False, is_staff=False)
    if curso_filtro:
        alumnos_qs = alumnos_qs.filter(curso=curso_filtro)

    alumnos = list(alumnos_qs.order_by('last_name', 'first_name'))
    alumnos_ids = [a.id for a in alumnos]

    total_actividades_sistema = Actividad.objects.filter(activo=True).count()

    # Mapeo de asistencias agregadas
    asistencias_stats = Asistencia.objects.filter(alumno_id__in=alumnos_ids).values('alumno_id').annotate(
        total=Count('id'),
        presentes=Count('id', filter=Q(estado__in=['PRESENTE', 'LLEGADA_TARDE']))
    )
    mapa_asistencia = {
        a['alumno_id']: round((a['presentes'] / a['total']) * 100) if a['total'] > 0 else 0
        for a in asistencias_stats
    }

    # Mapeo de actividades entregadas
    entregas_qs = EntregaActividad.objects.filter(
        estudiante_id__in=alumnos_ids,
        estado__in=['ENVIADO', 'CALIFICADO']
    ).select_related('actividad')

    mapa_entregas_objetos = {}
    mapa_entregas_ids = {}
    for entrega in entregas_qs:
        mapa_entregas_objetos.setdefault(entrega.estudiante_id, []).append(entrega)
        mapa_entregas_ids.setdefault(entrega.estudiante_id, set()).add(entrega.actividad_id)

    # Mapeo de teorías completadas
    teorias_qs = ProgresoTeoria.objects.filter(
        estudiante_id__in=alumnos_ids,
        completado=True
    ).values('estudiante_id', 'actividad_id')

    mapa_teorias_ids = {}
    for t in teorias_qs:
        mapa_teorias_ids.setdefault(t['estudiante_id'], set()).add(t['actividad_id'])

    reporte_alumnos = []
    for alumno in alumnos:
        porcentaje_asistencia = mapa_asistencia.get(alumno.id, 0)
        entregas_alumno = mapa_entregas_objetos.get(alumno.id, [])
        
        # Unión de conjuntos de actividades completadas para evitar duplicaciones
        actividades_resueltas = mapa_entregas_ids.get(alumno.id, set()) | mapa_teorias_ids.get(alumno.id, set())

        porcentaje_avance = (
            round((len(actividades_resueltas) / total_actividades_sistema) * 100)
            if total_actividades_sistema > 0 else 0
        )
        if porcentaje_avance > 100:
            porcentaje_avance = 100

        notas = [e.calificacion for e in entregas_alumno if e.calificacion is not None]
        promedio_notas = round(sum(notas) / len(notas), 1) if notas else 0.0

        reporte_alumnos.append({
            'alumno': alumno,
            'porcentaje_asistencia': porcentaje_asistencia,
            'porcentaje_avance': porcentaje_avance,
            'promedio_notas': promedio_notas,
            'entregas_detalle': entregas_alumno,
        })

    cursos_disponibles = list(
        Usuario.objects.exclude(curso__isnull=True)
        .exclude(curso__exact='')
        .values_list('curso', flat=True)
        .distinct()
    )

    contexto = {
        'reporte': reporte_alumnos,
        'cursos_disponibles': cursos_disponibles,
        'curso_seleccionado': curso_filtro,
    }
    return render(request, 'educacion/panel_avance.html', contexto)