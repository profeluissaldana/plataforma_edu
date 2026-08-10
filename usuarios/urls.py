from django.urls import path
from .views import cargar_usuarios_excel

from . import views

urlpatterns = [
    path(
        'login/',
        views.login_view,
        name='login'
    ),

    path(
        'logout/',
        views.logout_view,
        name='logout'
    ),

    path('cargar-masiva/', views.cargar_usuarios_excel, name='cargar_usuarios_excel'),
    path('descargar-plantilla/', views.descargar_plantilla_excel, name='descargar_plantilla_excel'),
    # Rutas de Gestión de Alumnos
    path('alumnos/', views.lista_alumnos, name='lista_alumnos'),
    path('alumnos/<int:pk>/editar/', views.editar_alumno, name='editar_alumno'),
    path('alumnos/<int:pk>/reset-password/', views.reset_password_alumno, name='reset_password_alumno'),
    path('alumnos/<int:pk>/eliminar/', views.eliminar_alumno, name='eliminar_alumno'),
    path('alumnos/exportar/excel/', views.exportar_alumnos_excel, name='exportar_alumnos_excel'),
    path('alumnos/exportar/pdf/', views.exportar_alumnos_pdf, name='exportar_alumnos_pdf'),
    path('asistencias/tomar/', views.tomar_asistencia, name='tomar_asistencia'),

]

