import os
import io
import pandas as pd
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.http import FileResponse, HttpResponse

from .forms import CargaMasivaUsuariosForm
from .models import Usuario


def descargar_plantilla_excel(request):
    # Ruta ajustada a la app 'usuarios'
    ruta_archivo = os.path.join(settings.BASE_DIR, 'usuarios', 'static', 'excel', 'plantilla_alumnos.xlsx')
    
    # 1. Si el archivo físico existe en la ruta usuarios/static/excel/, lo entrega directamente
    if os.path.exists(ruta_archivo):
        return FileResponse(
            open(ruta_archivo, 'rb'), 
            as_attachment=True, 
            filename='Plantilla_Carga_Alumnos.xlsx'
        )
    
    # 2. Si no lo encuentra, genera la plantilla en memoria dinámicamente
    data = {
        'username': ['alumno01', 'alumno02'],
        'password': ['Clave1234', 'Clave1234'],
        'email': ['alumno01@escuela.edu.ar', 'alumno02@escuela.edu.ar'],
        'first_name': ['Juan', 'María'],
        'last_name': ['Pérez', 'Gómez'],
        'dni': ['42123456', '43123457'],
        'curso': ['6to 1ra', '6to 1ra'],
        'dia_cursado': ['Lunes', 'Lunes']
    }
    
    df = pd.DataFrame(data)
    
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Alumnos')
    
    buffer.seek(0)
    
    response = HttpResponse(
        buffer.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="Plantilla_Carga_Alumnos.xlsx"'
    return response


def es_administrador(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


@login_required
@user_passes_test(es_administrador)
def cargar_usuarios_excel(request):
    if request.method == 'POST':
        form = CargaMasivaUsuariosForm(request.POST, request.FILES)
        if form.is_valid():
            archivo = request.FILES['archivo_excel']
            try:
                # Lectura nativa del archivo Excel (.xlsx)
                df = pd.read_excel(archivo)
                
                # Normalizar nombres de columnas a minúsculas
                df.columns = df.columns.str.strip().str.lower()

                usuarios_creados = 0
                errores = []

                for index, row in df.iterrows():
                    username = str(row.get('username', '')).strip()
                    password = str(row.get('password', '')).strip()

                    if not username or not password or username == 'nan':
                        continue

                    if Usuario.objects.filter(username=username).exists():
                        errores.append(f"El usuario '{username}' ya existe.")
                        continue

                    # Creación del usuario con los nuevos campos
                    usuario = Usuario(
                        username=username,
                        email=str(row.get('email', '')).strip() if pd.notna(row.get('email')) else '',
                        first_name=str(row.get('first_name', '')).strip() if pd.notna(row.get('first_name')) else '',
                        last_name=str(row.get('last_name', '')).strip() if pd.notna(row.get('last_name')) else '',
                        dni=str(int(row['dni'])) if pd.notna(row.get('dni')) and str(row.get('dni')).replace('.','').isdigit() else str(row.get('dni', '')).strip(),
                        curso=str(row.get('curso', '')).strip() if pd.notna(row.get('curso')) else '',
                        dia_cursado=str(row.get('dia_cursado', '')).strip() if pd.notna(row.get('dia_cursado')) else '',
                    )
                    usuario.set_password(password)
                    usuario.save()
                    usuarios_creados += 1

                if usuarios_creados > 0:
                    messages.success(request, f"Se crearon exitosamente {usuarios_creados} usuarios.")
                if errores:
                    messages.warning(request, f"Ocurrieron algunos inconvenientes: {', '.join(errores)}")

                return redirect('cargar_usuarios_excel')

            except Exception as e:
                messages.error(request, f"Error al procesar el archivo Excel: {str(e)}")
    else:
        form = CargaMasivaUsuariosForm()

    return render(request, 'usuarios/cargar_masiva.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        usuario = authenticate(
            request,
            username=username,
            password=password
        )

        if usuario is not None:
            login(
                request,
                usuario
            )
            return redirect(settings.LOGIN_REDIRECT_URL)

        error = 'Usuario o contraseña incorrectos.'

        return render(
            request,
            'usuarios/login.html',
            {
                'error': error
            }
        )

    return render(
        request,
        'usuarios/login.html'
    )


def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return redirect('login')
    return redirect('inicio')