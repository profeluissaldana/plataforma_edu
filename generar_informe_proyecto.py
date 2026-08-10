from pathlib import Path

# ==============================
# CONFIGURACIÓN
# ==============================

ROOT = Path(__file__).parent
SALIDA = ROOT / "informe_proyecto.md"

CARPETAS_EXCLUIDAS = {
    ".git",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    "node_modules",
    ".idea",
    ".vscode",
    "migrations",
    "media",
    "staticfiles",
}

ARCHIVOS_EXCLUIDOS = {
    "db.sqlite3",
    ".DS_Store",
}

EXTENSIONES_TEXTO = {
    ".py",
    ".html",
    ".css",
    ".js",
    ".json",
    ".txt",
    ".md",
    ".yml",
    ".yaml",
    ".toml",
    ".ini",
    ".cfg",
    ".env",
}

# ==============================
# ÁRBOL
# ==============================


def escribir_arbol(carpeta, prefijo=""):
    elementos = sorted(
        [
            e
            for e in carpeta.iterdir()
            if e.name not in CARPETAS_EXCLUIDAS
            and e.name not in ARCHIVOS_EXCLUIDOS
        ],
        key=lambda x: (x.is_file(), x.name.lower()),
    )

    for i, elemento in enumerate(elementos):
        ultimo = i == len(elementos) - 1
        rama = "└── " if ultimo else "├── "

        f.write(prefijo + rama + elemento.name + "\n")

        if elemento.is_dir():
            extension = "    " if ultimo else "│   "
            escribir_arbol(elemento, prefijo + extension)


# ==============================
# CONTENIDO ARCHIVOS
# ==============================


def recorrer(carpeta):

    elementos = sorted(carpeta.iterdir(), key=lambda x: str(x))

    for elemento in elementos:

        if elemento.name in CARPETAS_EXCLUIDAS:
            continue

        if elemento.name in ARCHIVOS_EXCLUIDOS:
            continue

        if elemento.is_dir():
            recorrer(elemento)
            continue

        if elemento.suffix.lower() not in EXTENSIONES_TEXTO:
            continue

        try:
            contenido = elemento.read_text(encoding="utf-8", errors="ignore")
        except:
            continue

        ruta = elemento.relative_to(ROOT)

        lineas = contenido.count("\n") + 1

        f.write("\n")
        f.write("=" * 90 + "\n")
        f.write(f"ARCHIVO: {ruta}\n")
        f.write(f"Líneas: {lineas}\n")
        f.write("=" * 90 + "\n\n")

        f.write("```")
        f.write(elemento.suffix.replace(".", ""))
        f.write("\n")

        f.write(contenido)

        f.write("\n```\n\n")


# ==============================
# RESUMEN Y ESTADÍSTICAS
# ==============================

estadisticas = {"archivos": 0, "python": 0, "html": 0, "css": 0, "js": 0}

for archivo in ROOT.rglob("*"):

    if any(parte in CARPETAS_EXCLUIDAS for parte in archivo.parts):
        continue

    if archivo.is_file():

        estadisticas["archivos"] += 1

        if archivo.suffix == ".py":
            estadisticas["python"] += 1

        elif archivo.suffix == ".html":
            estadisticas["html"] += 1

        elif archivo.suffix == ".css":
            estadisticas["css"] += 1

        elif archivo.suffix == ".js":
            estadisticas["js"] += 1

# ==============================
# GENERAR INFORME
# ==============================

with open(SALIDA, "w", encoding="utf-8") as f:

    # Encabezado con Contexto Semántico y Decisiones del Proyecto
    f.write("# CONTEXTO DEL PROYECTO: Plataforma Edu EETP N° 614\n\n")
    f.write("## Información General\n")
    f.write("- Framework: Django 5.2 (Python)\n")
    f.write(
        "- Proyecto: Plataforma Educativa para la EETP N° 614 (Santo"
        " Tomé).\n"
    )
    f.write("- Apps instaladas: `usuarios`, `educacion`, `comunicacion`.\n\n")

    f.write("## Decisiones Recientes de Código\n")
    f.write(
        "1. El modelo `Asistencia` pertenece a `usuarios.models` (se eliminó"
        " de `educacion.models`).\n"
    )
    f.write(
        "2. Las vistas de `educacion/views.py` gestionan entregas y progreso"
        " tanto para `Leccion` como para `Subleccion`.\n"
    )
    f.write(
        "3. `ckeditor` está integrado y su warning W001 fue silenciado en"
        " `settings.py`.\n\n"
    )

    f.write("---\n\n")

    # Métricas y Estadísticas
    f.write("# INFORME TÉCNICO DEL PROYECTO\n\n")
    f.write("## Resumen de Archivos\n\n")
    f.write(f"- Total archivos: {estadisticas['archivos']}\n")
    f.write(f"- Python: {estadisticas['python']}\n")
    f.write(f"- HTML: {estadisticas['html']}\n")
    f.write(f"- CSS: {estadisticas['css']}\n")
    f.write(f"- JavaScript: {estadisticas['js']}\n\n")

    # Árbol del directorio
    f.write("## Árbol del proyecto\n\n")
    f.write(ROOT.name + "\n")
    escribir_arbol(ROOT)

    # Código de archivos
    f.write("\n\n## Contenido de archivos\n")
    recorrer(ROOT)

print("\n=====================================")
print("Informe generado correctamente con encabezado de contexto.")
print(SALIDA)
print("=====================================")