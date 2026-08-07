from django.conf import settings
from django.db import models


class MensajeChat(models.Model):

    emisor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mensajes_enviados'
    )

    receptor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mensajes_recibidos'
    )

    contenido = models.TextField()

    fecha_envio = models.DateTimeField(
        auto_now_add=True
    )

    leido = models.BooleanField(
        default=False
    )

    class Meta:
        verbose_name = 'Mensaje de chat'
        verbose_name_plural = 'Mensajes de chat'
        ordering = ['fecha_envio']

    def __str__(self):
        return f"De {self.emisor} para {self.receptor} ({self.fecha_envio.strftime('%d/%m %H:%M')})"


class ConfiguracionPlataforma(models.Model):

    chat_habilitado = models.BooleanField(
        default=True,
        verbose_name="Habilitar Chat entre Usuarios"
    )

    intercambio_archivos_habilitado = models.BooleanField(
        default=True,
        verbose_name="Habilitar Intercambio de Archivos"
    )

    class Meta:
        verbose_name = 'Configuración de la plataforma'
        verbose_name_plural = 'Configuraciones de la plataforma'

    def __str__(self):
        return "Configuración Global de la Plataforma"