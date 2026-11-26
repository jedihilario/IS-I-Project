import os
import sys
from pathlib import Path

if getattr(sys, 'frozen', False):
    # En el ejecutable la base de datos se guarda junto al binario para que
    # persista entre ejecuciones (el paquete se extrae en un directorio temporal).
    database_path = Path(sys.executable).resolve().parent / 'dev.db'
    os.environ.setdefault('DEV_DATABASE_URL', f'sqlite:///{database_path}')

from is_i_project import main

if __name__ == '__main__':
    main()
