#Módulo para gestionar de manera segura los directorios y rutas

from pathlib import Path

# Obtener rutas de directorios estructurales del proyecto
DIR_BASE = Path(__file__).parent.parent
DIR_DATA = DIR_BASE / "data"
DIR_UTILS = DIR_BASE / "utils"
DIR_SRC = DIR_BASE / "src"

# Rutas a las carpetas de facturas en el directorio data
DIR_PENDIENTES = DIR_BASE / "data" / "facturas_pendientes"
DIR_PROCESADAS = DIR_BASE / "data" / "facturas_procesadas"

def init_directorios():
    """Inicializa los directorios no estructurales"""
    directorios = [
        DIR_PROCESADAS,
        DIR_PENDIENTES,
    ]

    for directorio in directorios:
        directorio.mkdir(parents=True,exist_ok=True)




