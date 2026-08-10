from django.urls import path

from . import views

app_name = 'comunicacion'

urlpatterns = [
    # Vista principal de la sala de chat
    path('chat/<int:espacio_id>/', views.sala_chat, name='sala_chat'),
    
    # Endpoints AJAX llamados por JavaScript (con nombres alineados a las plantillas)
    path(
        'chat/<int:espacio_id>/enviar/',
        views.enviar_mensaje_chat,
        name='enviar_mensaje_chat',
    ),
    path(
        'chat/<int:espacio_id>/alternar/',
        views.alternar_estado_chat,
        name='alternar_estado_chat',
    ),
    path(
        'chat/<int:espacio_id>/obtener/',
        views.obtener_mensajes_ajax,
        name='obtener_mensajes_ajax',
    ),

    # Alias de compatibilidad por si JS consulta las rutas relativas directamente sin 'chat/'
    path(
        '<int:espacio_id>/chat/obtener/',
        views.obtener_mensajes_ajax,
    ),
    path(
        '<int:espacio_id>/chat/alternar/',
        views.alternar_estado_chat,
    ),
    path(
        '<int:espacio_id>/chat/enviar/',
        views.enviar_mensaje_chat,
    ),
]