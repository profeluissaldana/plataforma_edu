from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings


class Usuario(AbstractUser):

    TURNOS = [
        ('M', 'Mañana'),
        ('T', 'Tarde'),
        ('N', 'Noche'),
    ]

    dni = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True
    )

    curso = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Ejemplo: 5A, 5C, 6to 1ra"
    )

    turno = models.CharField(
        max_length=1,
        choices=TURNOS,
        default='M',
        help_text="Turno al que pertenece el alumno (Mañana/Tarde/Noche)"
    )

    dia_cursado = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Ejemplo: Lunes, Miércoles o Lunes,Martes"
    )

    def __str__(self):
        nombre_completo = self.get_full_name()
        return f"{nombre_completo} ({self.username})" if nombre_completo else self.username


class HistorialSesion(models.Model):

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='historial_sesiones'
    )

    fecha_inicio = models.DateTimeField(
        auto_now_add=True
    )

    fecha_cierre = models.DateTimeField(
        null=True,
        blank=True
    )

    direccion_ip = models.GenericIPAddressField(
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Historial de sesión'
        verbose_name_plural = 'Historiales de sesiones'
        ordering = ['-fecha_inicio']

    def __str__(self):
        return f"{self.usuario.username} - {self.fecha_inicio.strftime('%d/%m/%Y %H:%M')}"


class Asistencia(models.Model):

    ESTADOS = [
        ('P', 'Presente'),
        ('A', 'Ausente'),
        ('T', 'Tarde'),
        ('J', 'Justificado'),
    ]

    alumno = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='asistencias'
    )

    fecha = models.DateField()

    estado = models.CharField(
        max_length=1,
        choices=ESTADOS,
        default='P'
    )

    observacion = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    class Meta:
        unique_together = ('alumno', 'fecha')
        verbose_name = 'Asistencia'
        verbose_name_plural = 'Asistencias'

    def __str__(self):
        return f"{self.alumno} - {self.fecha}: {self.get_estado_display()}"