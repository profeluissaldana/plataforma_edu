from django import forms
from .models import EntregaActividad  # O el modelo que maneje las entregas de los alumnos

class EntregaActividadForm(forms.ModelForm):
    class Meta:
        model = EntregaActividad
        fields = ['respuesta_texto', 'archivo_adjunto']
        widgets = {
            'respuesta_texto': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Escribe aquí tu respuesta o comentarios sobre la entrega...'
            }),
            'archivo_adjunto': forms.FileInput(attrs={
                'class': 'form-control'
            }),
        }