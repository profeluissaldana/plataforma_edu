from django.urls import path

from . import views

urlpatterns = [
    path(
        '',
        views.inicio,
        name='inicio'
    ),
    path(
        'espacio/<int:espacio_id>/',
        views.detalle_espacio,
        name='detalle_espacio'
    ),

    path(
        'actividad/<int:actividad_id>/', 
        views.realizar_actividad, 
        name='realizar_actividad'
        ),

    path(
        'actividad/<int:actividad_id>/marcar-teoria/', 
         views.marcar_teoria_completada, 
         name='marcar_teoria_completada'
         ),
]