from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):

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
        help_text="Ejemplo: 6to 1ra, 5to 2da"
    )

    dia_cursado = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Ejemplo: Lunes, Miércoles"
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