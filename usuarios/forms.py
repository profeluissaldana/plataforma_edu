from django import forms

class CargaMasivaUsuariosForm(forms.Form):
    archivo_excel = forms.FileField(
        label="Seleccionar archivo Excel (.xlsx o .xls)",
        help_text="El archivo debe contener las columnas: username, password, email, first_name, last_name, dni, curso, dia_cursado."
    )