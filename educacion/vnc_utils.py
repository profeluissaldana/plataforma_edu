import subprocess
import socket
import sys

# Diccionario en memoria para rastrear qué puerto tiene asignado cada IP
# { "192.168.1.12": 6081, ... }
VNC_PORT_MAPPING = {}

STARTING_PORT = 6081  # Empezamos después del 6080

def buscar_puerto_libre(puerto_inicial=STARTING_PORT):
    """Encuentra un puerto libre en el servidor para lanzar websockify."""
    puerto = puerto_inicial
    while puerto < 65000:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', puerto)) != 0:
                return puerto
            puerto += 1
    raise RuntimeError("No hay puertos disponibles")

def obtener_o_crear_puerto_vnc(ip_cliente):
    """Devuelve el puerto de Websockify asignado a la IP del alumno."""
    # Si ya hay un puerto activo para esta IP, lo reutilizamos
    if ip_cliente in VNC_PORT_MAPPING:
        puerto = VNC_PORT_MAPPING[ip_cliente]
        # Verificar si el proceso sigue respondiendo
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', puerto)) == 0:
                return puerto

    # Si no existe, buscamos un puerto nuevo y lanzamos websockify
    nuevo_puerto = buscar_puerto_libre()
    cmd = [
        sys.executable, "-m", "websockify",
        "--web", "static/novnc",
        str(nuevo_puerto),
        f"{ip_cliente}:5900"
    ]
    
    # Lanzamos el proceso en segundo plano de forma no bloqueante
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    VNC_PORT_MAPPING[ip_cliente] = nuevo_puerto
    return nuevo_puerto