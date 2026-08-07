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
]

