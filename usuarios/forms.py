from django import forms
from .models import Usuario

class CargaMasivaUsuariosForm(forms.Form):
    archivo_excel = forms.FileField(
        label="Seleccionar archivo Excel (.xlsx o .xls)",
        help_text="El archivo debe contener las columnas: username, password, email, first_name, last_name, dni, curso, turno, dia_cursado."
    )

# Formulario para editar datos de un alumno
class EditarUsuarioForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['username', 'first_name', 'last_name', 'email', 'dni', 'curso', 'turno', 'dia_cursado']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'dni': forms.TextInput(attrs={'class': 'form-control'}),
            'curso': forms.TextInput(attrs={'class': 'form-control'}),
            'turno': forms.Select(attrs={'class': 'form-select'}),
            'dia_cursado': forms.TextInput(attrs={'class': 'form-control'}),
        }

# Formulario para resetear contraseña
class ResetPasswordForm(forms.Form):
    nueva_password = forms.CharField(
        label="Nueva Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Ingresa la nueva contraseña'})
    )