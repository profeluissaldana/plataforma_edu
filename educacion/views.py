from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect, render

from .models import (
    Actividad,
    EntregaActividad,
    EspacioEducativo,
    Leccion,
    Modulo,
    Opcion,
    Pregunta,
    ProgresoTeoria,
    RespuestaUsuario,
)


# ==============================================================================
# HELPER: CÁLCULO DE PROGRESO Y ACTIVIDADES COMPLETADAS
# ==============================================================================
def obtener_progreso_estudiante(estudiante, espacio):
    """
    Calcula el porcentaje global de avance del alumno en un Espacio Educativo
    y devuelve la lista de IDs de actividades completadas.
    """
    total_actividades = Actividad.objects.filter(
        leccion__modulo__espacio_educativo=espacio,
        activo=True
    ).count()

    if total_actividades == 0:
        return 0, set()

    # IDs de Cuestionarios / Prácticas entregadas o aprobadas
    entregas_completas = EntregaActividad.objects.filter(
        estudiante=estudiante,
        actividad__leccion__modulo__espacio_educativo=espacio,
        estado__in=['ENVIADO', 'CALIFICADO']
    ).values_list('actividad_id', flat=True)

    # IDs de lecturas / videos de Teoría completados
    teorias_completas = ProgresoTeoria.objects.filter(
        estudiante=estudiante,
        actividad__leccion__modulo__espacio_educativo=espacio,
        completado=True
    ).values_list('actividad_id', flat=True)

    actividades_resueltas_ids = set(entregas_completas) | set(teorias_completas)
    
    porcentaje = round((len(actividades_resueltas_ids) / total_actividades) * 100)
    return porcentaje, actividades_resueltas_ids


# ==============================================================================
# VISTAS PRINCIPALES
# ==============================================================================
@login_required
def inicio(request):
    """
    Vista principal que lista los Espacios Educativos activos.
    """
    espacios = EspacioEducativo.objects.filter(activo=True)
    return render(
        request,
        'educacion/inicio.html',
        {
            'espacios': espacios
        }
    )


@login_required
def detalle_espacio(request, espacio_id):
    """
    Vista responsiva que muestra el detalle de un Espacio Educativo,
    calculando la barra de progreso global y las actividades completadas.
    """
    espacio = get_object_or_404(
        EspacioEducativo,
        id=espacio_id,
        activo=True
    )

    # Optimizamos la consulta trayendo módulos, lecciones y actividades ordenadas
    modulos = espacio.modulos.filter(
        activo=True
    ).order_by('orden').prefetch_related(
        Prefetch(
            'lecciones',
            queryset=Leccion.objects.filter(activo=True).order_by('orden')
        ),
        'lecciones__contenidos',
        'lecciones__actividades'
    )

    # Cálculo de porcentaje global e historial de completados
    porcentaje_avance, actividades_resueltas_ids = obtener_progreso_estudiante(request.user, espacio)

    return render(
        request,
        'educacion/detalle_espacio.html',
        {
            'espacio': espacio,
            'modulos': modulos,
            'porcentaje_avance': porcentaje_avance,
            'actividades_resueltas_ids': actividades_resueltas_ids,
        }
    )


@login_required
def marcar_teoria_completada(request, actividad_id):
    """
    Permite al alumno marcar una lectura o video como completado
    para avanzar en la secuencia pedagógica.
    """
    actividad = get_object_or_404(Actividad, id=actividad_id, activo=True)
    
    ProgresoTeoria.objects.get_or_create(
        estudiante=request.user,
        actividad=actividad,
        defaults={'completado': True}
    )
    
    messages.success(request, f'¡Excelente! Has completado: {actividad.titulo}')
    return redirect('detalle_espacio', espacio_id=actividad.leccion.modulo.espacio_educativo.id)


@login_required
def realizar_actividad(request, actividad_id):
    """
    Vista polimórfica para:
    1) Entregar archivos de código / ejercicios prácticos.
    2) Responder cuestionarios con clave de acceso.
    """
    actividad = get_object_or_404(
        Actividad.objects.prefetch_related(
            Prefetch(
                'preguntas',
                queryset=Pregunta.objects.filter(activo=True).order_by('orden').prefetch_related('opciones')
            )
        ),
        id=actividad_id,
        activo=True
    )

    # Crear o recuperar el registro de entrega del usuario
    entrega, _ = EntregaActividad.objects.get_or_create(
        actividad=actividad,
        estudiante=request.user
    )

    # -------------------------------------------------------------
    # CASO 1: YA FUE ENVIADO -> Mostrar resultado o confirmación
    # -------------------------------------------------------------
    if entrega.estado in ['ENVIADO', 'CALIFICADO']:
        puntaje_obtenido = entrega.calificacion or entrega.puntaje_obtenido or 0
        puntaje_total = sum(p.puntaje for p in actividad.preguntas.all()) or 1
        porcentaje = round((puntaje_obtenido / puntaje_total) * 100, 1) if actividad.preguntas.exists() else 100

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
            }
        )

    # -------------------------------------------------------------
    # CASO 2: PROCESAR PRÁCTICA DE PROGRAMACIÓN (SUBIDA DE ARCHIVO)
    # -------------------------------------------------------------
    if actividad.tipo == 'PRACTICA':
        if request.method == 'POST' and 'btn_subir_practica' in request.POST:
            archivo = request.FILES.get('archivo_adjunto')
            comentario = request.POST.get('comentario_estudiante', '').strip()

            if archivo:
                entrega.archivo_adjunto = archivo
                entrega.comentario_estudiante = comentario
                entrega.estado = 'ENVIADO'
                entrega.save()

                messages.success(request, '¡Tu archivo de práctica ha sido subido con éxito!')
                return redirect('realizar_actividad', actividad_id=actividad.id)
            else:
                messages.error(request, 'Debes adjuntar un archivo para poder realizar la entrega.')

        return render(
            request,
            'educacion/realizar_actividad.html',
            {
                'actividad': actividad,
                'entrega': entrega,
                'es_practica': True,
                'ya_enviado': False,
            }
        )

    # -------------------------------------------------------------
    # CASO 3: VALIDACIÓN DE CLAVE DE ACCESO (CUESTIONARIOS)
    # -------------------------------------------------------------
    session_key = f'actividad_clave_validada_{actividad.id}'
    tiene_clave = bool(actividad.clave_acceso and actividad.clave_acceso.strip())
    clave_validada = request.session.get(session_key, False)

    if tiene_clave and not clave_validada:
        if request.method == 'POST' and 'btn_validar_clave' in request.POST:
            clave_ingresada = request.POST.get('clave_acceso', '').strip()
            if clave_ingresada == actividad.clave_acceso.strip():
                request.session[session_key] = True
                messages.success(request, '¡Clave correcta! Puedes comenzar la evaluación.')
                return redirect('realizar_actividad', actividad_id=actividad.id)
            else:
                messages.error(request, 'La clave ingresada es incorrecta.')

        return render(
            request,
            'educacion/realizar_actividad.html',
            {
                'actividad': actividad,
                'requiere_clave': True,
                'ya_enviado': False,
            }
        )

    # -------------------------------------------------------------
    # CASO 4: PROCESAR EL ENVÍO DEL CUESTIONARIO (POST)
    # -------------------------------------------------------------
    if request.method == 'POST' and 'btn_enviar_respuestas' in request.POST:
        puntaje_total_obtenido = 0

        with transaction.atomic():
            for pregunta in actividad.preguntas.all():
                campo_name = f'pregunta_{pregunta.id}'

                # Para OPCION_MULTIPLE o VERDADERO_FALSO
                if pregunta.tipo in ['OPCION_MULTIPLE', 'VERDADERO_FALSO']:
                    opcion_id = request.POST.get(campo_name)
                    if opcion_id:
                        opcion_obj = Opcion.objects.filter(id=opcion_id, pregunta=pregunta).first()
                        RespuestaUsuario.objects.update_or_create(
                            entrega=entrega,
                            pregunta=pregunta,
                            defaults={'opcion_seleccionada': opcion_obj}
                        )
                        if opcion_obj and opcion_obj.es_correcta:
                            puntaje_total_obtenido += pregunta.puntaje

                # Para RESPUESTA_CORTA o RESPUESTA_LARGA
                elif pregunta.tipo in ['RESPUESTA_CORTA', 'RESPUESTA_LARGA']:
                    texto = request.POST.get(campo_name, '').strip()
                    if texto:
                        RespuestaUsuario.objects.update_or_create(
                            entrega=entrega,
                            pregunta=pregunta,
                            defaults={'texto_respuesta': texto}
                        )

            entrega.estado = 'ENVIADO'
            entrega.calificacion = puntaje_total_obtenido
            entrega.puntaje_obtenido = puntaje_total_obtenido
            entrega.save()

        # Limpiar la clave de la sesión al finalizar la entrega
        if session_key in request.session:
            del request.session[session_key]

        messages.success(request, '¡Tus respuestas han sido guardadas y enviadas correctamente!')
        return redirect('realizar_actividad', actividad_id=actividad.id)

    # -------------------------------------------------------------
    # CASO 5: MOSTRAR PREGUNTAS DEL CUESTIONARIO
    # -------------------------------------------------------------
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
        }
    )