from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):

    fieldsets = (
        *UserAdmin.fieldsets,
        (
            'Información institucional',
            {
                'fields': (
                    'dni',
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
                ),
            },
        ),
    )