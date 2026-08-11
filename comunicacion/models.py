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


class PermisoChat(models.Model):
    sala = models.CharField(max_length=100, db_index=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='permisos_chat')
    puede_hablar = models.BooleanField(default=True)
    ultima_conexion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Permiso de Chat'
        verbose_name_plural = 'Permisos de Chat'
        unique_together = ('sala', 'usuario')

    def __str__(self):
        estado = "Autorizado" if self.puede_hablar else "Silenciado"
        return f'{self.usuario} en {self.sala}: {estado}'


class RegistroPresencia(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='registros_presencia')
    hora_ingreso = models.DateTimeField(auto_now_add=True)
    ultima_actividad = models.DateTimeField(auto_now=True)
    ip_origen = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        verbose_name = 'Registro de Presencia'
        verbose_name_plural = 'Registros de Presencia'
        ordering = ['-ultima_actividad']

    def __str__(self):
        return f'{self.usuario} - Conectado desde: {self.hora_ingreso.strftime("%H:%M:%S")}'