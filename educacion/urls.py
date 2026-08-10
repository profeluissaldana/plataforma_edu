from django.urls import path

from . import views

# Define el namespace para resolver 'educacion:inicio', 'educacion:detalle_espacio', etc.
app_name = 'educacion'

urlpatterns = [
    # --- RUTAS DE LA PLATAFORMA EDUCATIVA ---
    path('', views.inicio, name='inicio'),
    path(
        'espacio/<int:espacio_id>/',
        views.detalle_espacio,
        name='detalle_espacio',
    ),
    path(
        'actividad/<int:actividad_id>/',
        views.realizar_actividad,
        name='realizar_actividad',
    ),
    path(
        'actividad/<int:actividad_id>/marcar-teoria/',
        views.marcar_teoria_completada,
        name='marcar_teoria_completada',
    ),
    path('git-github/', views.git_github_view, name='git_github'),
    path(
        'html-css/modulo-1/',
        views.html_css_modulo1_view,
        name='html_css_modulo1',
    ),
    # --- PANEL DE GESTIÓN PEDAGÓGICA Y ASISTENCIA ---
    path(
        'gestion/asistencia-jornada/',
        views.tomar_asistencia_jornada,
        name='tomar_asistencia_jornada',
    ),
    path('gestion/grupos/', views.ver_grupos, name='ver_grupos'),
    path(
        'gestion/historial/',
        views.historial_asistencias,
        name='historial_asistencias',
    ),
    path(
        'gestion/reiniciar-ciclo/',
        views.reiniciar_ciclo_lectivo,
        name='reiniciar_ciclo_lectivo',
    ),
]