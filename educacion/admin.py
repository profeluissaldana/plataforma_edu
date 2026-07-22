from django.contrib import admin

from .models import (
    EspacioEducativo,
    Modulo,
    Leccion,
    Contenido,
    Actividad,
    Pregunta,
    Opcion,
)


@admin.register(EspacioEducativo)
class EspacioEducativoAdmin(admin.ModelAdmin):

    list_display = (
        'nombre',
        'fecha_creacion',
        'activo',
    )

    list_filter = (
        'activo',
        'fecha_creacion',
    )

    search_fields = (
        'nombre',
        'descripcion',
    )


@admin.register(Modulo)
class ModuloAdmin(admin.ModelAdmin):

    list_display = (
        'nombre',
        'espacio_educativo',
        'orden',
        'activo',
    )

    list_filter = (
        'activo',
        'espacio_educativo',
    )

    search_fields = (
        'nombre',
        'descripcion',
    )


@admin.register(Leccion)
class LeccionAdmin(admin.ModelAdmin):

    list_display = (
        'titulo',
        'modulo',
        'orden',
        'activo',
    )

    list_filter = (
        'activo',
        'modulo',
    )

    search_fields = (
        'titulo',
        'descripcion',
    )


@admin.register(Contenido)
class ContenidoAdmin(admin.ModelAdmin):

    list_display = (
        'titulo',
        'leccion',
        'tipo',
        'orden',
        'activo',
    )

    list_filter = (
        'tipo',
        'activo',
    )

    search_fields = (
        'titulo',
        'contenido',
    )


class OpcionInline(admin.TabularInline):

    model = Opcion

    extra = 4


class PreguntaInline(admin.StackedInline):

    model = Pregunta

    extra = 1


@admin.register(Actividad)
class ActividadAdmin(admin.ModelAdmin):

    list_display = (
        'titulo',
        'leccion',
        'tipo',
        'orden',
        'fecha_limite',
        'activo',
    )

    list_filter = (
        'tipo',
        'activo',
    )

    search_fields = (
        'titulo',
        'descripcion',
    )

    inlines = [
        PreguntaInline,
    ]


@admin.register(Pregunta)
class PreguntaAdmin(admin.ModelAdmin):

    list_display = (
        'texto',
        'actividad',
        'tipo',
        'orden',
        'puntaje',
        'activo',
    )

    list_filter = (
        'tipo',
        'activo',
    )

    search_fields = (
        'texto',
    )

    inlines = [
        OpcionInline,
    ]


@admin.register(Opcion)
class OpcionAdmin(admin.ModelAdmin):

    list_display = (
        'texto',
        'pregunta',
        'es_correcta',
        'orden',
    )

    list_filter = (
        'es_correcta',
    )

    search_fields = (
        'texto',
    )