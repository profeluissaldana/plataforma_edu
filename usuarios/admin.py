from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, HistorialSesion


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):

    fieldsets = (
        *UserAdmin.fieldsets,
        (
            'Información institucional',
            {
                'fields': (
                    'dni',
                    'curso',
                    'dia_cursado',
                ),
            },
        ),
    )

    add_fieldsets = (
        *UserAdmin.add_fieldsets,
        (
            'Información institucional',
            {
                'fields': (
                    'dni',
                    'curso',
                    'dia_cursado',
                ),
            },
        ),
    )

    list_display = ('username', 'first_name', 'last_name', 'dni', 'curso', 'dia_cursado', 'is_staff')
    search_fields = ('username', 'first_name', 'last_name', 'dni', 'curso')


@admin.register(HistorialSesion)
class HistorialSesionAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'fecha_inicio', 'fecha_cierre', 'direccion_ip')
    list_filter = ('fecha_inicio', 'usuario')
    search_fields = ('usuario__username', 'usuario__first_name', 'usuario__last_name', 'direccion_ip')
    readonly_fields = ('usuario', 'fecha_inicio', 'fecha_cierre', 'direccion_ip')