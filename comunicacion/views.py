from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST, require_GET

from .models import MensajeChat


@login_required
def sala_chat(request, espacio_id):
    sala_nombre = f'espacio_{espacio_id}'
    mensajes = MensajeChat.objects.filter(sala=sala_nombre).order_by('fecha_envio')
    es_docente = request.user.is_staff or request.user.is_superuser

    # Leemos el estado del chat desde la sesión (por defecto Habilitado: True)
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
    # Obtener el contenido enviado por FormData o POST directo
    contenido = (request.POST.get('contenido') or request.POST.get('mensaje') or '').strip()
    
    if not contenido:
        return JsonResponse({'status': 'error', 'error': 'El mensaje no puede estar vacío.'}, status=400)

    try:
        # Detectar dinámicamente si el modelo usa 'remitente' o 'usuario'
        campos_modelo = [f.name for f in MensajeChat._meta.get_fields()]
        datos_mensaje = {
            'sala': f'espacio_{espacio_id}',
            'contenido': contenido,
        }
        
        if 'remitente' in campos_modelo:
            datos_mensaje['remitente'] = request.user
        elif 'usuario' in campos_modelo:
            datos_mensaje['usuario'] = request.user

        msg = MensajeChat.objects.create(**datos_mensaje)

        nombre_usuario = request.user.get_full_name() or request.user.username

        return JsonResponse({
            'status': 'ok',
            'usuario': nombre_usuario,
            'contenido': msg.contenido,
            'fecha_envio': msg.fecha_envio.strftime('%H:%M') if hasattr(msg, 'fecha_envio') else ''
        })

    except Exception as e:
        return JsonResponse({'status': 'error', 'error': str(e)}, status=500)

@login_required
@require_POST
def alternar_estado_chat(request, espacio_id):
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse(
            {'status': 'error', 'error': 'No autorizado'}, status=403
        )

    clave_sesion = f'chat_habilitado_{espacio_id}'
    estado_actual = request.session.get(clave_sesion, True)
    nuevo_estado = not estado_actual
    request.session[clave_sesion] = nuevo_estado

    return JsonResponse({'status': 'ok', 'chat_habilitado': nuevo_estado})


@login_required
@require_GET
def obtener_mensajes_ajax(request, espacio_id):
    clave_sesion = f'chat_habilitado_{espacio_id}'
    chat_habilitado = request.session.get(clave_sesion, True)

    sala_nombre = f'espacio_{espacio_id}'
    mensajes_qs = MensajeChat.objects.filter(sala=sala_nombre).order_by('fecha_envio')

    lista_mensajes = []
    for m in mensajes_qs:
        remitente_obj = getattr(m, 'remitente', None) or getattr(m, 'usuario', None)
        nombre = (remitente_obj.get_full_name() or remitente_obj.username) if remitente_obj else 'Anónimo'
        
        lista_mensajes.append({
            'id': m.id,
            'usuario': nombre,
            'es_mio': remitente_obj == request.user if remitente_obj else False,
            'contenido': m.contenido,
            'fecha_envio': m.fecha_envio.strftime('%H:%M') if hasattr(m, 'fecha_envio') else '',
        })

    return JsonResponse(
        {
            'status': 'ok',
            'chat_habilitado': chat_habilitado,
            'mensajes': lista_mensajes,
        }
    )