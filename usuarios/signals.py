from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.contrib.sessions.models import Session
from django.utils import timezone
from .models import HistorialSesion


def get_client_ip(request):
    """Obtiene la dirección IP real del cliente."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@receiver(user_logged_in)
def handle_user_login(sender, request, user, **kwargs):
    """
    1. Previene múltiples inicios de sesión simultáneos invalidando sesiones anteriores.
    2. Registra el inicio de sesión en el modelo HistorialSesion.
    """
    # 1. Prevenir sesiones concurrentes
    current_session_key = request.session.session_key
    active_sessions = Session.objects.filter(expire_date__gte=timezone.now())

    for session in active_sessions:
        session_data = session.get_decoded()
        if session_data.get('_auth_user_id') == str(user.id):
            if session.session_key != current_session_key:
                session.delete()

    # 2. Registrar en HistorialSesion y guardar la clave de sesión activa
    ip = get_client_ip(request)
    historial = HistorialSesion.objects.create(
        usuario=user,
        direccion_ip=ip
    )
    request.session['historial_sesion_id'] = historial.id


@receiver(user_logged_out)
def handle_user_logout(sender, request, user, **kwargs):
    """
    Registra la fecha y hora exacta de cierre de sesión.
    """
    if request and hasattr(request, 'session'):
        historial_id = request.session.get('historial_sesion_id')
        if historial_id:
            try:
                historial = HistorialSesion.objects.get(id=historial_id)
                historial.fecha_cierre = timezone.now()
                historial.save()
            except HistorialSesion.DoesNotExist:
                pass