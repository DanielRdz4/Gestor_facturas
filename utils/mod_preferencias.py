#Módulo para gestionar las preferencias de usuario
import os
import shutil

directorio_actual = os.curdir()
directorio_carpeta = "data"
ruta = os.path.join(directorio_actual,directorio_carpeta)

if os.path.exists(ruta):
    pass