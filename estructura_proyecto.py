from pathlib import Path

# Carpeta raíz del proyecto (donde está este script)
ROOT = Path(__file__).parent

# Carpetas a ignorar
IGNORAR_CARPETAS = {
    ".git",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".idea",
    ".vscode",
    "node_modules",
    "migrations",       # quitar esta línea si quieres ver las migraciones
    "media",
    "staticfiles"
}

# Archivos a ignorar
IGNORAR_ARCHIVOS = {
    ".DS_Store",
    "db.sqlite3",
}

# Extensiones a ignorar
IGNORAR_EXTENSIONES = {
    ".pyc",
    ".pyo",
    ".log",
}


def mostrar_arbol(carpeta: Path, prefijo=""):
    elementos = sorted(
        carpeta.iterdir(),
        key=lambda x: (x.is_file(), x.name.lower())
    )

    elementos = [
        e for e in elementos
        if e.name not in IGNORAR_CARPETAS
        and e.name not in IGNORAR_ARCHIVOS
        and e.suffix not in IGNORAR_EXTENSIONES
    ]

    for i, elemento in enumerate(elementos):
        ultimo = i == len(elementos) - 1
        rama = "└── " if ultimo else "├── "

        salida.write(prefijo + rama + elemento.name + "\n")

        if elemento.is_dir():
            extension = "    " if ultimo else "│   "
            mostrar_arbol(elemento, prefijo + extension)


with open("estructura_proyecto.txt", "w", encoding="utf-8") as salida:
    salida.write(ROOT.name + "/\n")
    mostrar_arbol(ROOT)

print("\nEstructura generada correctamente.")
print("Archivo creado: estructura_proyecto.txt")