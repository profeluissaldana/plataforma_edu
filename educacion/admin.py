from django.contrib import admin

from .models import EspacioEducativo


@admin.register(EspacioEducativo)
class EspacioEducativoAdmin(admin.ModelAdmin):

    list_display = (
        'nombre',
        'activo',
        'fecha_creacion',
    )

    list_filter = (
        'activo',
    )

    search_fields = (
        'nombre',
        'descripcion',
    )