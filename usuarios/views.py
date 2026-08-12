import io
import json
import os
from datetime import date, datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import FileResponse, HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from .forms import CargaMasivaUsuariosForm, EditarUsuarioForm, ResetPasswordForm
from .models import Asistencia, HistorialSesion, Usuario

DIAS_MAP = {
    0: 'Lunes',
    1: 'Martes',
    2: 'Miércoles',
    3: 'Jueves',
    4: 'Viernes',
    5: 'Sábado',
    6: 'Domingo',
}


def es_administrador(user):
  return user.is_authenticated and (user.is_staff or user.is_superuser)


@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def tomar_asistencia(request):
  fecha_str = request.GET.get('fecha', date.today().isoformat())
  curso_filtro = request.GET.get('curso', '')
  turno_filtro = request.GET.get('turno', '')

  cursos = (
      Usuario.objects.filter(is_superuser=False, is_staff=False)
      .values_list('curso', flat=True)
      .distinct()
  )

  alumnos = []

  # Obtener el día de la semana
  nombre_dia = ''
  if fecha_str:
    try:
      fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d').date()
      nombre_dia = DIAS_MAP.get(fecha_obj.weekday(), '')
    except ValueError:
      pass

  if curso_filtro:
    # Consulta base filtrando por curso
    alumnos_qs = Usuario.objects.filter(
        is_superuser=False, is_staff=False, curso__iexact=curso_filtro.strip()
    )

    # Filtro por Turno (Mañana / Tarde / Noche) si se selecciona
    if turno_filtro:
      alumnos_qs = alumnos_qs.filter(turno=turno_filtro)

    # Filtro flexible para el día: busca coincidencias (ej: 'Lunes') o incluye vacíos
    if nombre_dia:
      nombre_dia_limpio = nombre_dia.replace('é', 'e').replace('É', 'E')
      alumnos_qs = alumnos_qs.filter(
          Q(dia_cursado__icontains=nombre_dia)
          | Q(dia_cursado__icontains=nombre_dia_limpio)
          | Q(dia_cursado__isnull=True)
          | Q(dia_cursado='')
      )

    alumnos = alumnos_qs.order_by('last_name', 'first_name')

  if request.method == 'POST':
    fecha_post = request.POST.get('fecha')
    curso_post = request.POST.get('curso')
    turno_post = request.POST.get('turno', '')

    nombre_dia_post = ''
    if fecha_post:
      try:
        fecha_obj_post = datetime.strptime(fecha_post, '%Y-%m-%d').date()
        nombre_dia_post = DIAS_MAP.get(fecha_obj_post.weekday(), '')
      except ValueError:
        pass

    alumnos_post = Usuario.objects.filter(
        is_superuser=False, is_staff=False, curso__iexact=curso_post.strip()
    )

    if turno_post:
      alumnos_post = alumnos_post.filter(turno=turno_post)

    if nombre_dia_post:
      nombre_dia_limpio = nombre_dia_post.replace('é', 'e').replace('É', 'E')
      alumnos_post = alumnos_post.filter(
          Q(dia_cursado__icontains=nombre_dia_post)
          | Q(dia_cursado__icontains=nombre_dia_limpio)
          | Q(dia_cursado__isnull=True)
          | Q(dia_cursado='')
      )

    for alumno in alumnos_post:
      estado = request.POST.get(f'estado_{alumno.id}', 'P')
      observacion = request.POST.get(f'obs_{alumno.id}', '')

      Asistencia.objects.update_or_create(
          alumno=alumno,
          fecha=fecha_post,
          defaults={'estado': estado, 'observacion': observacion},
      )

    messages.success(
        request,
        f'Asistencias guardadas correctamente para {curso_post} el'
        f' {fecha_post}.',
    )
    url_redirect = f'{request.path}?curso={curso_post}&fecha={fecha_post}'
    if turno_post:
      url_redirect += f'&turno={turno_post}'
    return redirect(url_redirect)

  # Cargar asistencias preexistentes
  asistencias_existentes = {}
  if curso_filtro and alumnos:
    registros = Asistencia.objects.filter(
        alumno__in=alumnos, fecha=fecha_str
    )
    asistencias_existentes = {a.alumno_id: a for a in registros}

  alumnos_data = []
  for a in alumnos:
    asist = asistencias_existentes.get(a.id)
    alumnos_data.append({
        'alumno': a,
        'estado': asist.estado if asist else 'P',
        'observacion': asist.observacion if asist else '',
    })

  context = {
      'cursos': sorted([c for c in cursos if c]),
      'curso_filtro': curso_filtro,
      'turno_filtro': turno_filtro,
      'turnos': Usuario.TURNOS,
      'fecha': fecha_str,
      'nombre_dia': nombre_dia,
      'alumnos_data': alumnos_data,
  }
  return render(request, 'asistencias/tomar_asistencia.html', context)


def descargar_plantilla_excel(request):
  ruta_archivo = os.path.join(
      settings.BASE_DIR,
      'usuarios',
      'static',
      'excel',
      'plantilla_alumnos.xlsx',
  )

  if os.path.exists(ruta_archivo):
    return FileResponse(
        open(ruta_archivo, 'rb'),
        as_attachment=True,
        filename='Plantilla_Carga_Alumnos.xlsx',
    )

  data = {
      'username': ['alumno01', 'alumno02', 'alumno03'],
      'password': ['Clave1234', 'Clave1234', 'Clave1234'],
      'email': [
          'alumno01@escuela.edu.ar',
          'alumno02@escuela.edu.ar',
          'alumno03@escuela.edu.ar',
      ],
      'first_name': ['Juan', 'María', 'Carlos'],
      'last_name': ['Pérez', 'Gómez', 'López'],
      'dni': ['42123456', '43123457', '44123458'],
      'curso': ['5A', '5A', '6B'],
      'turno': ['Mañana', 'Tarde', 'Noche'],
      'dia_cursado': ['Lunes,Miércoles', 'Martes,Jueves', 'Viernes'],
  }

  df = pd.DataFrame(data)

  buffer = io.BytesIO()
  with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
    df.to_excel(writer, index=False, sheet_name='Alumnos')

  buffer.seek(0)

  response = HttpResponse(
      buffer.getvalue(),
      content_type=(
          'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      ),
  )
  response['Content-Disposition'] = (
      'attachment; filename="Plantilla_Carga_Alumnos.xlsx"'
  )
  return response


@login_required
@user_passes_test(es_administrador)
def cargar_usuarios_excel(request):
  if request.method == 'POST':
    form = CargaMasivaUsuariosForm(request.POST, request.FILES)
    if form.is_valid():
      archivo = request.FILES['archivo_excel']
      try:
        df = pd.read_excel(archivo)
        df.columns = df.columns.str.strip().str.lower()

        usuarios_creados = 0
        errores = []

        TURNO_MAP = {
            'M': 'M',
            'MAÑANA': 'M',
            'MANANA': 'M',
            'T': 'T',
            'TARDE': 'T',
            'N': 'N',
            'NOCHE': 'N',
        }

        for index, row in df.iterrows():
          username = str(row.get('username', '')).strip()
          password = str(row.get('password', '')).strip()

          if not username or not password or username == 'nan':
            continue

          if Usuario.objects.filter(username=username).exists():
            errores.append(f"El usuario '{username}' ya existe.")
            continue

          turno_raw = str(row.get('turno', '')).strip().upper()
          turno_val = TURNO_MAP.get(turno_raw, 'M')

          usuario = Usuario(
              username=username,
              email=(
                  str(row.get('email', '')).strip()
                  if pd.notna(row.get('email'))
                  else ''
              ),
              first_name=(
                  str(row.get('first_name', '')).strip()
                  if pd.notna(row.get('first_name'))
                  else ''
              ),
              last_name=(
                  str(row.get('last_name', '')).strip()
                  if pd.notna(row.get('last_name'))
                  else ''
              ),
              dni=(
                  str(int(row['dni']))
                  if pd.notna(row.get('dni'))
                  and str(row.get('dni')).replace('.', '').isdigit()
                  else str(row.get('dni', '')).strip()
              ),
              curso=(
                  str(row.get('curso', '')).strip()
                  if pd.notna(row.get('curso'))
                  else ''
              ),
              turno=turno_val,
              dia_cursado=(
                  str(row.get('dia_cursado', '')).strip()
                  if pd.notna(row.get('dia_cursado'))
                  else ''
              ),
          )
          usuario.set_password(password)
          usuario.save()
          usuarios_creados += 1

        if usuarios_creados > 0:
          messages.success(
              request,
              f'Se crearon exitosamente {usuarios_creados} usuarios.',
          )
        if errores:
          messages.warning(
              request,
              f"Ocurrieron algunos inconvenientes: {', '.join(errores)}",
          )

        return redirect('cargar_usuarios_excel')

      except Exception as e:
        messages.error(
            request, f'Error al procesar el archivo Excel: {str(e)}'
        )
  else:
    form = CargaMasivaUsuariosForm()

  return render(request, 'usuarios/cargar_masiva.html', {'form': form})


def login_view(request):
  if request.method == 'POST':
    username = request.POST.get('username')
    password = request.POST.get('password')
    equipo = request.POST.get('equipo')

    # Si la petición viene en formato JSON (ej. mediante API o script)
    if not username and request.content_type == 'application/json':
      try:
        body_data = json.loads(request.body)
        username = body_data.get('username')
        password = body_data.get('password')
        equipo = body_data.get('equipo')
      except json.JSONDecodeError:
        pass

    usuario = authenticate(request, username=username, password=password)

    if usuario is not None:
      login(request, usuario)

      # 1. Obtener la IP del cliente
      x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
      if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
      else:
        ip = request.META.get('REMOTE_ADDR')

      ahora = timezone.now()
      equipo_nombre = equipo.strip() if equipo else 'Desconocido'

      # 2. Actualizar estado del modelo Usuario
      usuario.ultimo_equipo = equipo_nombre
      usuario.ultima_conexion = ahora
      usuario.save(update_fields=['ultimo_equipo', 'ultima_conexion'])

      # 3. Registrar el ingreso en HistorialSesion
      HistorialSesion.objects.create(
          usuario=usuario, equipo=equipo_nombre, direccion_ip=ip
      )

      return redirect(settings.LOGIN_REDIRECT_URL)

    error = 'Usuario o contraseña incorrectos.'
    return render(request, 'usuarios/login.html', {'error': error})

  return render(request, 'usuarios/login.html')


def logout_view(request):
  if request.method == 'POST':
    logout(request)
    return redirect('login')
  return redirect('inicio')


@login_required
@user_passes_test(es_administrador)
def lista_alumnos(request):
  busqueda = request.GET.get('q', '').strip()
  curso_filtro = request.GET.get('curso', '').strip()
  dia_filtro = request.GET.get('dia_cursado', '').strip()
  turno_filtro = request.GET.get('turno', '').strip()
  order_by = request.GET.get('order_by', 'last_name')

  # Filtrar solo alumnos (excluir superusuarios y personal de staff)
  alumnos = Usuario.objects.filter(is_superuser=False, is_staff=False)

  if busqueda:
    alumnos = alumnos.filter(
        Q(first_name__icontains=busqueda)
        | Q(last_name__icontains=busqueda)
        | Q(dni__icontains=busqueda)
        | Q(username__icontains=busqueda)
    )

  if curso_filtro:
    alumnos = alumnos.filter(curso__icontains=curso_filtro)

  if dia_filtro:
    alumnos = alumnos.filter(dia_cursado__icontains=dia_filtro)

  if turno_filtro:
    alumnos = alumnos.filter(turno=turno_filtro)

  # Ordenamiento seguro
  campos_validos = [
      'username',
      '-username',
      'last_name',
      '-last_name',
      'first_name',
      '-first_name',
      'dni',
      '-dni',
      'curso',
      '-curso',
      'dia_cursado',
      '-dia_cursado',
      'turno',
      '-turno',
  ]
  if order_by in campos_validos:
    alumnos = alumnos.order_by(order_by)
  else:
    alumnos = alumnos.order_by('last_name', 'first_name')

  # Paginación (10 alumnos por página)
  paginator = Paginator(alumnos, 10)
  page_number = request.GET.get('page')
  page_obj = paginator.get_page(page_number)

  # Listas dinámicas para filtros
  cursos = (
      Usuario.objects.filter(is_superuser=False, is_staff=False)
      .values_list('curso', flat=True)
      .distinct()
  )
  dias = (
      Usuario.objects.filter(is_superuser=False, is_staff=False)
      .values_list('dia_cursado', flat=True)
      .distinct()
  )

  context = {
      'page_obj': page_obj,
      'alumnos': page_obj.object_list,
      'busqueda': busqueda,
      'curso_filtro': curso_filtro,
      'dia_filtro': dia_filtro,
      'turno_filtro': turno_filtro,
      'order_by': order_by,
      'cursos': sorted(filter(None, cursos)),
      'dias': sorted(filter(None, dias)),
      'turnos': Usuario.TURNOS,
  }
  return render(request, 'usuarios/lista_alumnos.html', context)


@login_required
@user_passes_test(es_administrador)
def editar_alumno(request, pk):
  alumno = Usuario.objects.get(pk=pk)
  if request.method == 'POST':
    form = EditarUsuarioForm(request.POST, instance=alumno)
    if form.is_valid():
      form.save()
      messages.success(
          request,
          f'Se actualizaron los datos de'
          f' {alumno.get_full_name() or alumno.username}.',
      )
      return redirect('lista_alumnos')
  else:
    form = EditarUsuarioForm(instance=alumno)
  return render(
      request, 'usuarios/editar_alumno.html', {'form': form, 'alumno': alumno}
  )


@login_required
@user_passes_test(es_administrador)
def reset_password_alumno(request, pk):
  alumno = Usuario.objects.get(pk=pk)
  if request.method == 'POST':
    form = ResetPasswordForm(request.POST)
    if form.is_valid():
      nueva_clave = form.cleaned_data['nueva_password']
      alumno.set_password(nueva_clave)
      alumno.save()
      messages.success(
          request,
          'Contraseña actualizada con éxito para el usuario'
          f" '{alumno.username}'.",
      )
      return redirect('lista_alumnos')
  else:
    form = ResetPasswordForm()
  return render(
      request,
      'usuarios/reset_password.html',
      {'form': form, 'alumno': alumno},
  )


@login_required
@user_passes_test(es_administrador)
def eliminar_alumno(request, pk):
  alumno = Usuario.objects.get(pk=pk)
  if request.method == 'POST':
    nombre = alumno.get_full_name() or alumno.username
    alumno.delete()
    messages.success(
        request, f'El alumno {nombre} fue eliminado correctamente.'
    )
    return redirect('lista_alumnos')
  return render(request, 'usuarios/eliminar_alumno.html', {'alumno': alumno})


@login_required
@user_passes_test(es_administrador)
def exportar_alumnos_excel(request):
  busqueda = request.GET.get('q', '').strip()
  curso_filtro = request.GET.get('curso', '').strip()
  dia_filtro = request.GET.get('dia_cursado', '').strip()
  turno_filtro = request.GET.get('turno', '').strip()

  alumnos = Usuario.objects.filter(is_superuser=False, is_staff=False)

  if busqueda:
    alumnos = alumnos.filter(
        Q(first_name__icontains=busqueda)
        | Q(last_name__icontains=busqueda)
        | Q(dni__icontains=busqueda)
        | Q(username__icontains=busqueda)
    )
  if curso_filtro:
    alumnos = alumnos.filter(curso__icontains=curso_filtro)
  if dia_filtro:
    alumnos = alumnos.filter(dia_cursado__icontains=dia_filtro)
  if turno_filtro:
    alumnos = alumnos.filter(turno=turno_filtro)

  data = []
  for a in alumnos:
    data.append({
        'Usuario': a.username,
        'Nombre': a.first_name,
        'Apellido': a.last_name,
        'DNI': a.dni or '',
        'Email': a.email or '',
        'Curso': a.curso or '',
        'Turno': a.get_turno_display(),
        'Día Cursado': a.dia_cursado or '',
    })

  df = pd.DataFrame(data)

  buffer = io.BytesIO()
  with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
    df.to_excel(writer, index=False, sheet_name='Reporte_Alumnos')

  buffer.seek(0)

  response = HttpResponse(
      buffer.getvalue(),
      content_type=(
          'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      ),
  )
  response['Content-Disposition'] = (
      'attachment; filename="Reporte_Alumnos.xlsx"'
  )
  return response


@login_required
@user_passes_test(es_administrador)
def exportar_alumnos_pdf(request):
  busqueda = request.GET.get('q', '').strip()
  curso_filtro = request.GET.get('curso', '').strip()
  dia_filtro = request.GET.get('dia_cursado', '').strip()
  turno_filtro = request.GET.get('turno', '').strip()

  alumnos = Usuario.objects.filter(is_superuser=False, is_staff=False)

  if busqueda:
    alumnos = alumnos.filter(
        Q(first_name__icontains=busqueda)
        | Q(last_name__icontains=busqueda)
        | Q(dni__icontains=busqueda)
        | Q(username__icontains=busqueda)
    )
  if curso_filtro:
    alumnos = alumnos.filter(curso__icontains=curso_filtro)
  if dia_filtro:
    alumnos = alumnos.filter(dia_cursado__icontains=dia_filtro)
  if turno_filtro:
    alumnos = alumnos.filter(turno=turno_filtro)

  buffer = io.BytesIO()
  doc = SimpleDocTemplate(
      buffer,
      pagesize=letter,
      rightMargin=30,
      leftMargin=30,
      topMargin=30,
      bottomMargin=30,
  )

  elements = []
  styles = getSampleStyleSheet()

  title_style = ParagraphStyle(
      'TitleStyle',
      parent=styles['Heading1'],
      fontSize=16,
      leading=20,
      textColor=colors.HexColor('#0d6efd'),
      spaceAfter=10,
  )

  elements.append(Paragraph('Reporte de Alumnos Registrados', title_style))

  subtitulo = 'Filtros aplicados: '
  detalles_filtros = []
  if curso_filtro:
    detalles_filtros.append(f'Curso: {curso_filtro}')
  if turno_filtro:
    detalles_filtros.append(f'Turno: {turno_filtro}')
  if dia_filtro:
    detalles_filtros.append(f'Día: {dia_filtro}')
  if busqueda:
    detalles_filtros.append(f"Búsqueda: '{busqueda}'")

  subtitulo += (
      ', '.join(detalles_filtros)
      if detalles_filtros
      else 'Ninguno (Todos los alumnos)'
  )
  elements.append(Paragraph(subtitulo, styles['Normal']))
  elements.append(Spacer(1, 15))

  table_data = [
      ['Usuario', 'Nombre Completo', 'DNI', 'Curso', 'Turno', 'Día Cursado']
  ]

  for a in alumnos:
    nombre_completo = f'{a.last_name} {a.first_name}'.strip() or '-'
    table_data.append([
        a.username,
        nombre_completo,
        a.dni or '-',
        a.curso or '-',
        a.get_turno_display(),
        a.dia_cursado or '-',
    ])

  tabla = Table(table_data, colWidths=[90, 160, 70, 70, 70, 90])
  tabla.setStyle(
      TableStyle([
          ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d6efd')),
          ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
          ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
          ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
          ('FONTSIZE', (0, 0), (-1, -1), 9),
          ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
          ('TOPPADDING', (0, 0), (-1, 0), 8),
          ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
          (
              'ROWBACKGROUNDS',
              (0, 1),
              (-1, -1),
              [colors.white, colors.HexColor('#f8f9fa')],
          ),
      ])
  )

  elements.append(tabla)
  doc.build(elements)

  buffer.seek(0)
  response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
  response['Content-Disposition'] = 'inline; filename="Reporte_Alumnos.pdf"'
  return response