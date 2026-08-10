from django.contrib import admin

from .models import ArchivoCompartido, MensajeChat


@admin.register(MensajeChat)
class MensajeChatAdmin(admin.ModelAdmin):
    list_display = ('remitente', 'sala', 'contenido', 'fecha_envio')
    list_filter = ('sala', 'fecha_envio')
    search_fields = ('contenido', 'remitente__username', 'remitente__first_name')


@admin.register(ArchivoCompartido)
class ArchivoCompartidoAdmin(admin.ModelAdmin):
    list_display = ('remitente', 'destinatario', 'descripcion', 'fecha_subida')
    list_filter = ('fecha_subida',)
    search_fields = ('descripcion', 'remitente__username')