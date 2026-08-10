from django.contrib.auth import get_user_model
from django.db import models

Usuario = get_user_model()


class MensajeChat(models.Model):
    remitente = models.ForeignKey(
        Usuario, on_delete=models.CASCADE, related_name='mensajes_enviados'
    )
    sala = models.CharField(
        max_length=100,
        default='general',
        help_text='Identificador de la sala de chat (ej: general, curso_python, etc.)',
    )
    contenido = models.TextField()
    fecha_envio = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Mensaje de Chat'
        verbose_name_plural = 'Mensajes de Chat'
        ordering = ['fecha_envio']

    def __str__(self):
        return f'[{self.sala}] {self.remitente}: {self.contenido[:30]}'


class ArchivoCompartido(models.Model):
    remitente = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='comunicacion_archivos_enviados',
    )
    destinatario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='comunicacion_archivos_recibidos',
        null=True,
        blank=True,
        help_text='Dejar vacío para transmitir a todos los estudiantes.',
    )
    archivo = models.FileField(upload_to='comunicacion/archivos/')
    descripcion = models.CharField(max_length=255, blank=True)
    fecha_subida = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Archivo Compartido'
        verbose_name_plural = 'Archivos Compartidos'
        ordering = ['-fecha_subida']

    def __str__(self):
        return f'De {self.remitente} - {self.descripcion or self.archivo.name}'