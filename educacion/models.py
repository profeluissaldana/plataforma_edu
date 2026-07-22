from django.conf import settings
from django.db import models


class EspacioEducativo(models.Model):

    nombre = models.CharField(
        max_length=200
    )

    descripcion = models.TextField(
        blank=True
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True
    )

    activo = models.BooleanField(
        default=True
    )

    class Meta:
        verbose_name = 'Espacio educativo'
        verbose_name_plural = 'Espacios educativos'

    def __str__(self):
        return self.nombre


class Modulo(models.Model):

    espacio_educativo = models.ForeignKey(
        EspacioEducativo,
        on_delete=models.CASCADE,
        related_name='modulos'
    )

    nombre = models.CharField(
        max_length=200
    )

    descripcion = models.TextField(
        blank=True
    )

    orden = models.PositiveIntegerField(
        default=1
    )

    activo = models.BooleanField(
        default=True
    )

    class Meta:
        verbose_name = 'Módulo'
        verbose_name_plural = 'Módulos'

    def __str__(self):
        return f'{self.espacio_educativo} - {self.nombre}'


class Leccion(models.Model):

    modulo = models.ForeignKey(
        Modulo,
        on_delete=models.CASCADE,
        related_name='lecciones'
    )

    titulo = models.CharField(
        max_length=200
    )

    descripcion = models.TextField(
        blank=True
    )

    orden = models.PositiveIntegerField(
        default=1
    )

    activo = models.BooleanField(
        default=True
    )

    class Meta:
        verbose_name = 'Lección'
        verbose_name_plural = 'Lecciones'

    def __str__(self):
        return f'{self.modulo} - {self.titulo}'


class Contenido(models.Model):

    TIPO_CONTENIDO = [
        ('TEXTO', 'Texto'),
        ('VIDEO', 'Video'),
        ('IMAGEN', 'Imagen'),
        ('ARCHIVO', 'Archivo'),
        ('CODIGO', 'Código'),
    ]

    leccion = models.ForeignKey(
        Leccion,
        on_delete=models.CASCADE,
        related_name='contenidos'
    )

    titulo = models.CharField(
        max_length=200
    )

    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CONTENIDO
    )

    contenido = models.TextField(
        blank=True
    )

    url = models.URLField(
        blank=True
    )

    orden = models.PositiveIntegerField(
        default=1
    )

    activo = models.BooleanField(
        default=True
    )

    class Meta:
        verbose_name = 'Contenido'
        verbose_name_plural = 'Contenidos'

    def __str__(self):
        return f'{self.leccion} - {self.titulo}'


class Actividad(models.Model):

    TIPO_ACTIVIDAD = [
        ('EJERCICIO', 'Ejercicio'),
        ('CUESTIONARIO', 'Cuestionario'),
        ('ENTREGA', 'Entrega'),
    ]

    leccion = models.ForeignKey(
        Leccion,
        on_delete=models.CASCADE,
        related_name='actividades'
    )

    titulo = models.CharField(
        max_length=200
    )

    descripcion = models.TextField(
        blank=True
    )

    tipo = models.CharField(
        max_length=20,
        choices=TIPO_ACTIVIDAD
    )

    orden = models.PositiveIntegerField(
        default=1
    )

    fecha_limite = models.DateTimeField(
        null=True,
        blank=True
    )

    activo = models.BooleanField(
        default=True
    )

    class Meta:
        verbose_name = 'Actividad'
        verbose_name_plural = 'Actividades'

    def __str__(self):
        return f'{self.leccion} - {self.titulo}'


class Pregunta(models.Model):

    TIPO_PREGUNTA = [
        ('OPCION_MULTIPLE', 'Opción múltiple'),
        ('VERDADERO_FALSO', 'Verdadero o falso'),
        ('RESPUESTA_CORTA', 'Respuesta corta'),
        ('RESPUESTA_LARGA', 'Respuesta larga'),
    ]

    actividad = models.ForeignKey(
        Actividad,
        on_delete=models.CASCADE,
        related_name='preguntas'
    )

    texto = models.TextField()

    tipo = models.CharField(
        max_length=30,
        choices=TIPO_PREGUNTA
    )

    orden = models.PositiveIntegerField(
        default=1
    )

    puntaje = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=1
    )

    activo = models.BooleanField(
        default=True
    )

    class Meta:
        verbose_name = 'Pregunta'
        verbose_name_plural = 'Preguntas'

    def __str__(self):
        return f'{self.actividad} - Pregunta {self.orden}'


class Opcion(models.Model):

    pregunta = models.ForeignKey(
        Pregunta,
        on_delete=models.CASCADE,
        related_name='opciones'
    )

    texto = models.CharField(
        max_length=300
    )

    es_correcta = models.BooleanField(
        default=False
    )

    orden = models.PositiveIntegerField(
        default=1
    )

    class Meta:
        verbose_name = 'Opción'
        verbose_name_plural = 'Opciones'

    def __str__(self):
        return f'{self.pregunta} - {self.texto}'


class Inscripcion(models.Model):

    ESTADO_INSCRIPCION = [
        ('ACTIVA', 'Activa'),
        ('FINALIZADA', 'Finalizada'),
        ('CANCELADA', 'Cancelada'),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='inscripciones'
    )

    espacio_educativo = models.ForeignKey(
        EspacioEducativo,
        on_delete=models.CASCADE,
        related_name='inscripciones'
    )

    fecha_inscripcion = models.DateTimeField(
        auto_now_add=True
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADO_INSCRIPCION,
        default='ACTIVA'
    )

    class Meta:
        verbose_name = 'Inscripción'
        verbose_name_plural = 'Inscripciones'

    def __str__(self):
        return (
            f'{self.usuario} - '
            f'{self.espacio_educativo}'
        )