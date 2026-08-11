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
    path(
        'chat/<int:espacio_id>/permiso/<int:usuario_id>/',
        views.alternar_permiso_usuario,
        name='alternar_permiso_usuario',
    ),

    # Panel e Informes de Usuarios Conectados (Independiente del Chat)
    path('monitoreo/usuarios/', views.panel_usuarios_conectados, name='panel_usuarios_conectados'),
    path('monitoreo/usuarios/api/', views.api_usuarios_conectados, name='api_usuarios_conectados'),
    path('presencia/ping/', views.registrar_ping_presencia, name='registrar_ping_presencia'),

    # Alias de compatibilidad
    path('<int:espacio_id>/chat/obtener/', views.obtener_mensajes_ajax),
    path('<int:espacio_id>/chat/alternar/', views.alternar_estado_chat),
    path('<int:espacio_id>/chat/enviar/', views.enviar_mensaje_chat),
    path('<int:espacio_id>/chat/permiso/<int:usuario_id>/', views.alternar_permiso_usuario),
]