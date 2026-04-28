# Ejecutar con python test template dir.py para verificar que la variable de entorno y la ruta de templates son correctas.

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

templates_dir = os.getenv("PPTX_TEMPLATES_DIR")
print("=== Verificación de Templates ===")
print(f"Variable de entorno PPTX_TEMPLATES_DIR: {templates_dir}")
print(f"Ruta: {templates_dir}")
print(f"Existe: {Path(templates_dir).exists()}")
print(f"Contenido: {list(Path(templates_dir).glob('*.pptx'))}")