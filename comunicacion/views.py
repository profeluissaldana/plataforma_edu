from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST, require_GET

from .models import MensajeChat, PermisoChat, RegistroPresencia


@login_required
def sala_chat(request, espacio_id):
    sala_nombre = f'espacio_{espacio_id}'
    mensajes = MensajeChat.objects.filter(sala=sala_nombre).order_by('fecha_envio')
    es_docente = request.user.is_staff or request.user.is_superuser

    PermisoChat.objects.update_or_create(
        sala=sala_nombre,
        usuario=request.user,
        defaults={'ultima_conexion': timezone.now()}
    )

    clave_sesion = f'chat_habilitado_{espacio_id}'
    chat_habilitado = request.session.get(clave_sesion, True)

    contexto = {
        'espacio': {'id': espacio_id, 'nombre': f'Espacio {espacio_id}'},
        'mensajes': mensajes,
        'es_docente': es_docente,
        'chat_habilitado': chat_habilitado,
    }
    return render(request, 'comunicacion/sala_chat.html', contexto)


@login_required
@require_POST
def enviar_mensaje_chat(request, espacio_id):
    sala_nombre = f'espacio_{espacio_id}'
    es_docente = request.user.is_staff or request.user.is_superuser

    if not es_docente:
        permiso, _ = PermisoChat.objects.get_or_create(
            sala=sala_nombre, usuario=request.user
        )
        if not permiso.puede_hablar:
            return JsonResponse(
                {'status': 'error', 'error': 'No tienes autorización para enviar mensajes en este chat.'},
                status=403
            )

    contenido = (request.POST.get('contenido') or request.POST.get('mensaje') or '').strip()
    
    if not contenido:
        return JsonResponse({'status': 'error', 'error': 'El mensaje no puede estar vacío.'}, status=400)

    try:
        campos_modelo = [f.name for f in MensajeChat._meta.get_fields()]
        datos_mensaje = {
            'sala': sala_nombre,
            'contenido': contenido,
        }
        
        if 'remitente' in campos_modelo:
            datos_mensaje['remitente'] = request.user
        elif 'usuario' in campos_modelo:
            datos_mensaje['usuario'] = request.user

        msg = MensajeChat.objects.create(**datos_mensaje)
        nombre_usuario = request.user.get_full_name() or request.user.username

        # Convertir a hora local antes de formatear
        fecha_local = timezone.localtime(msg.fecha_envio) if hasattr(msg, 'fecha_envio') else None

        return JsonResponse({
            'status': 'ok',
            'usuario': nombre_usuario,
            'contenido': msg.contenido,
            'fecha_envio': fecha_local.strftime('%H:%M') if fecha_local else ''
        })

    except Exception as e:
        return JsonResponse({'status': 'error', 'error': str(e)}, status=500)


@login_required
@require_POST
def alternar_estado_chat(request, espacio_id):
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'status': 'error', 'error': 'No autorizado'}, status=403)

    clave_sesion = f'chat_habilitado_{espacio_id}'
    estado_actual = request.session.get(clave_sesion, True)
    nuevo_estado = not estado_actual
    request.session[clave_sesion] = nuevo_estado

    return JsonResponse({'status': 'ok', 'chat_habilitado': nuevo_estado})


@login_required
@require_POST
def alternar_permiso_usuario(request, espacio_id, usuario_id):
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'status': 'error', 'error': 'No autorizado'}, status=403)

    sala_nombre = f'espacio_{espacio_id}'
    permiso, _ = PermisoChat.objects.get_or_create(
        sala=sala_nombre,
        usuario_id=usuario_id
    )
    permiso.puede_hablar = not permiso.puede_hablar
    permiso.save()

    return JsonResponse({
        'status': 'ok',
        'usuario_id': usuario_id,
        'puede_hablar': permiso.puede_hablar
    })


@login_required
@require_GET
def obtener_mensajes_ajax(request, espacio_id):
    sala_nombre = f'espacio_{espacio_id}'

    permiso_actual, _ = PermisoChat.objects.get_or_create(
        sala=sala_nombre, usuario=request.user
    )
    permiso_actual.ultima_conexion = timezone.now()
    permiso_actual.save(update_fields=['ultima_conexion'])

    clave_sesion = f'chat_habilitado_{espacio_id}'
    chat_habilitado = request.session.get(clave_sesion, True)

    mensajes_qs = MensajeChat.objects.filter(sala=sala_nombre).order_by('fecha_envio')

    lista_mensajes = []
    for m in mensajes_qs:
        remitente_obj = getattr(m, 'remitente', None) or getattr(m, 'usuario', None)
        nombre = (remitente_obj.get_full_name() or remitente_obj.username) if remitente_obj else 'Anónimo'
        fecha_local = timezone.localtime(m.fecha_envio) if hasattr(m, 'fecha_envio') else None
        
        lista_mensajes.append({
            'id': m.id,
            'usuario': nombre,
            'es_mio': remitente_obj == request.user if remitente_obj else False,
            'contenido': m.contenido,
            'fecha_envio': fecha_local.strftime('%H:%M') if fecha_local else '',
        })

    limite_actividad = timezone.now() - timedelta(seconds=10)
    conectados_qs = PermisoChat.objects.filter(
        sala=sala_nombre,
        ultima_conexion__gte=limite_actividad
    ).select_related('usuario')

    lista_usuarios = [
        {
            'id': p.usuario.id,
            'nombre': p.usuario.get_full_name() or p.usuario.username,
            'es_docente': p.usuario.is_staff or p.usuario.is_superuser,
            'puede_hablar': p.puede_hablar,
            'es_yo': p.usuario == request.user,
        }
        for p in conectados_qs
    ]

    return JsonResponse(
        {
            'status': 'ok',
            'chat_habilitado': chat_habilitado,
            'puede_hablar_mi_usuario': permiso_actual.puede_hablar,
            'mensajes': lista_mensajes,
            'usuarios_conectados': lista_usuarios,
        }
    )


# =========================================================================
# VISTAS DE PRESENCIA Y MONITOREO GENERAL (INDEPENDIENTES DEL CHAT)
# =========================================================================

@login_required
@require_POST
def registrar_ping_presencia(request):
    """Endpoint llamado automáticamente en segundo plano por base.html."""
    ip = request.META.get('REMOTE_ADDR')
    cinco_horas_atras = timezone.now() - timedelta(hours=5)

    registro = RegistroPresencia.objects.filter(
        usuario=request.user,
        ultima_actividad__gte=cinco_horas_atras
    ).first()

    if registro:
        registro.ultima_actividad = timezone.now()
        registro.save(update_fields=['ultima_actividad'])
    else:
        RegistroPresencia.objects.create(usuario=request.user, ip_origen=ip)

    return JsonResponse({'status': 'ok'})


@login_required
def panel_usuarios_conectados(request):
    """Vista principal del panel para Docentes/Admins."""
    if not (request.user.is_staff or request.user.is_superuser):
        return render(request, '403.html', status=403)

    return render(request, 'comunicacion/usuarios_conectados.html')


@login_required
@require_GET
def api_usuarios_conectados(request):
    """Devuelve usuarios activos en los últimos 2 minutos con su Curso y Turno."""
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'status': 'error', 'error': 'No autorizado'}, status=403)

    hace_dos_minutos = timezone.now() - timedelta(minutes=2)
    
    registros = RegistroPresencia.objects.filter(
        ultima_actividad__gte=hace_dos_minutos
    ).select_related('usuario').order_by('-hora_ingreso')

    lista_usuarios = []
    total_alumnos = 0
    total_docentes = 0

    for reg in registros:
        u = reg.usuario
        es_doc = u.is_staff or u.is_superuser
        
        if es_doc:
            total_docentes += 1
            curso_info = "Docente / Personal Administrativo"
        else:
            total_alumnos += 1
            curso_str = u.curso if u.curso else "Sin Curso"
            turno_str = u.get_turno_display() if hasattr(u, 'get_turno_display') else ""
            curso_info = f"{curso_str} - Turno {turno_str}" if turno_str else curso_str

        segundos_inactivo = int((timezone.now() - reg.ultima_actividad).total_seconds())

        # Conversión explícita a la zona horaria local (Argentina)
        ingreso_local = timezone.localtime(reg.hora_ingreso)

        lista_usuarios.append({
            'id': u.id,
            'nombre_completo': u.get_full_name() or u.username,
            'username': u.username,
            'dni': u.dni or 'Sin DNI',
            'es_docente': es_doc,
            'curso': curso_info,
            'hora_ingreso': ingreso_local.strftime('%H:%M:%S'),
            'fecha_ingreso': ingreso_local.strftime('%d/%m/%Y'),
            'hace_cuanto': f"Hace {segundos_inactivo}s"
        })

    return JsonResponse({
        'status': 'ok',
        'totales': {
            'total_general': len(lista_usuarios),
            'total_alumnos': total_alumnos,
            'total_docentes': total_docentes
        },
        'usuarios': lista_usuarios
    })