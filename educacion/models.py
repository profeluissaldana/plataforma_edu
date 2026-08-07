from django.conf import settings
from django.db import models
from ckeditor.fields import RichTextField


class EspacioEducativo(models.Model):

    nombre = models.CharField(
        max_length=200
    )

    descripcion = RichTextField(
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

    descripcion = RichTextField(
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

    descripcion = RichTextField(
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


class Subleccion(models.Model):

    leccion = models.ForeignKey(
        Leccion,
        on_delete=models.CASCADE,
        related_name='sublecciones'
    )

    titulo = models.CharField(
        max_length=200
    )

    descripcion = RichTextField(
        blank=True
    )

    orden = models.PositiveIntegerField(
        default=1
    )

    activo = models.BooleanField(
        default=True
    )

    class Meta:
        ordering = ['orden']
        verbose_name = 'Sublección'
        verbose_name_plural = 'Sublecciones'

    def __str__(self):
        return f"{self.leccion.titulo} - Parte {self.orden}: {self.titulo}"


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
        related_name='contenidos',
        null=True,
        blank=True
    )

    subleccion = models.ForeignKey(
        Subleccion,
        on_delete=models.CASCADE,
        related_name='contenidos',
        null=True,
        blank=True
    )

    titulo = models.CharField(
        max_length=200
    )

    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CONTENIDO
    )

    contenido = RichTextField(
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
        padre = self.leccion or self.subleccion
        return f'{padre} - {self.titulo}'


class Actividad(models.Model):

    TIPO_ACTIVIDAD = [
        ('TEORIA', 'Lectura / Video'),
        ('PRACTICA', 'Práctica de Programación (Subida de Archivo)'),
        ('CUESTIONARIO', 'Cuestionario / Multiple Choice'),
        ('EJERCICIO', 'Ejercicio'),
        ('ENTREGA', 'Entrega'),
    ]

    leccion = models.ForeignKey(
        Leccion,
        on_delete=models.CASCADE,
        related_name='actividades',
        null=True,
        blank=True
    )

    subleccion = models.ForeignKey(
        Subleccion,
        on_delete=models.CASCADE,
        related_name='actividades',
        null=True,
        blank=True
    )

    titulo = models.CharField(
        max_length=200
    )

    descripcion = RichTextField(
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

    clave_acceso = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Clave requerida para que el alumno pueda iniciar el cuestionario en clase."
    )

    activo = models.BooleanField(
        default=True
    )

    class Meta:
        verbose_name = 'Actividad'
        verbose_name_plural = 'Actividades'

    def __str__(self):
        padre = self.leccion or self.subleccion
        return f'{padre} - {self.titulo}'


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

    texto = RichTextField()

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
        return f'{self.usuario} - {self.espacio_educativo}'


class EntregaActividad(models.Model):

    ESTADO_ENTREGA = [
        ('EN_PROCESO', 'En proceso'),
        ('ENVIADO', 'Enviado'),
        ('CALIFICADO', 'Calificado'),
    ]

    actividad = models.ForeignKey(
        Actividad,
        on_delete=models.CASCADE,
        related_name='entregas'
    )

    estudiante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='entregas_actividades'
    )

    fecha_envio = models.DateTimeField(
        auto_now=True
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADO_ENTREGA,
        default='EN_PROCESO'
    )

    archivo_adjunto = models.FileField(
        upload_to='entregas_alumnos/',
        blank=True,
        null=True,
        help_text="Archivo de código o práctico entregado por el estudiante."
    )

    comentario_estudiante = models.TextField(
        blank=True,
        null=True
    )

    puntaje_obtenido = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )

    calificacion = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Entrega de actividad'
        verbose_name_plural = 'Entregas de actividades'
        unique_together = ('actividad', 'estudiante')

    def __str__(self):
        return f'{self.estudiante} - {self.actividad}'


class RespuestaUsuario(models.Model):

    entrega = models.ForeignKey(
        EntregaActividad,
        on_delete=models.CASCADE,
        related_name='respuestas'
    )

    pregunta = models.ForeignKey(
        Pregunta,
        on_delete=models.CASCADE,
        related_name='respuestas_usuarios'
    )

    opcion_seleccionada = models.ForeignKey(
        Opcion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='seleccionada_en'
    )

    texto_respuesta = models.TextField(
        blank=True
    )

    class Meta:
        verbose_name = 'Respuesta de usuario'
        verbose_name_plural = 'Respuestas de usuarios'

    def __str__(self):
        return f'{self.entrega} - Pregunta: {self.pregunta.orden}'


class ProgresoTeoria(models.Model):

    estudiante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='progresos_teoria'
    )

    actividad = models.ForeignKey(
        Actividad,
        on_delete=models.CASCADE,
        related_name='progresos_teoria'
    )

    completado = models.BooleanField(
        default=False
    )

    fecha_completado = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        verbose_name = 'Progreso de teoría'
        verbose_name_plural = 'Progresos de teorías'
        unique_together = ('estudiante', 'actividad')

    def __str__(self):
        return f'{self.estudiante} - {self.actividad.titulo} (Completado: {self.completado})'


class IntercambioArchivo(models.Model):

    remitente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='archivos_enviados'
    )

    destinatario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='archivos_recibidos',
        null=True,
        blank=True,
        help_text="Dejar vacío si el archivo es público para todos los alumnos"
    )

    archivo = models.FileField(
        upload_to='intercambio_archivos/'
    )

    descripcion = models.CharField(
        max_length=255,
        blank=True
    )

    fecha_subida = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        verbose_name = 'Intercambio de archivo'
        verbose_name_plural = 'Intercambio de archivos'
        ordering = ['-fecha_subida']

    def __str__(self):
        return f"De {self.remitente} - {self.descripcion or self.archivo.name}"