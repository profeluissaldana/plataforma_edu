from django.contrib import admin
from .models import (
    Actividad,
    Contenido,
    EntregaActividad,
    EspacioEducativo,
    Leccion,
    Modulo,
    Opcion,
    Pregunta,
    RespuestaUsuario,
)


# ==============================================================================
# CONFIGURACIÓN DE MODELOS EDUCATIVOS
# ==============================================================================

@admin.register(EspacioEducativo)
class EspacioEducativoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activo')
    list_filter = ('activo',)
    search_fields = ('nombre', 'descripcion')


@admin.register(Modulo)
class ModuloAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'espacio_educativo', 'orden', 'activo')
    list_filter = ('activo', 'espacio_educativo')
    search_fields = ('nombre', 'descripcion')
    ordering = ('espacio_educativo', 'orden')


@admin.register(Leccion)
class LeccionAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'modulo', 'orden', 'activo')
    list_filter = ('activo', 'modulo__espacio_educativo')
    search_fields = ('titulo', 'descripcion')
    ordering = ('modulo', 'orden')


@admin.register(Contenido)
class ContenidoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'leccion', 'tipo', 'orden', 'activo')
    list_filter = ('tipo', 'activo', 'leccion__modulo__espacio_educativo')
    search_fields = ('titulo', 'texto')


# ==============================================================================
# CONFIGURACIÓN DE EVALUACIONES Y PREGUNTAS
# ==============================================================================

class OpcionInline(admin.TabularInline):
    model = Opcion
    extra = 3


@admin.register(Actividad)
class ActividadAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'leccion', 'tipo', 'clave_acceso', 'fecha_limite', 'activo')
    list_filter = ('tipo', 'activo', 'leccion__modulo__espacio_educativo')
    search_fields = ('titulo', 'descripcion', 'clave_acceso')


@admin.register(Pregunta)
class PreguntaAdmin(admin.ModelAdmin):
    list_display = ('texto', 'actividad', 'tipo', 'puntaje', 'orden', 'activo')
    list_filter = ('tipo', 'activo', 'actividad')
    search_fields = ('texto',)
    inlines = [OpcionInline]


@admin.register(Opcion)
class OpcionAdmin(admin.ModelAdmin):
    list_display = ('texto', 'pregunta', 'es_correcta')
    list_filter = ('es_correcta', 'pregunta__actividad')
    search_fields = ('texto',)


# ==============================================================================
# GESTIÓN DE ENTREGAS Y REINICIO DE EVALUACIONES
# ==============================================================================

@admin.register(EntregaActividad)
class EntregaActividadAdmin(admin.ModelAdmin):
    list_display = ('estudiante', 'actividad', 'estado', 'calificacion')
    list_filter = ('estado', 'actividad')
    search_fields = (
        'estudiante__username',
        'estudiante__first_name',
        'estudiante__last_name',
        'actividad__titulo'
    )
    actions = ['reiniciar_entrega']

    @admin.action(description='🔄 Reiniciar entrega (Permitir nuevo intento)')
    def reiniciar_entrega(self, request, queryset):
        cant = queryset.count()
        for entrega in queryset:
            # Eliminamos las respuestas enviadas por el alumno
            RespuestaUsuario.objects.filter(entrega=entrega).delete()
            # Reseteamos el estado y la calificación
            entrega.estado = 'EN_PROCESO'
            entrega.calificacion = None
            entrega.save()

        self.message_user(
            request,
            f"Se ha(n) reiniciado exitosamente {cant} entrega(s). El alumno ya puede volver a realizar el cuestionario."
        )


@admin.register(RespuestaUsuario)
class RespuestaUsuarioAdmin(admin.ModelAdmin):
    list_display = ('entrega', 'pregunta', 'opcion_seleccionada', 'texto_respuesta')
    list_filter = ('pregunta__actividad',)
    search_fields = ('entrega__estudiante__username', 'texto_respuesta')