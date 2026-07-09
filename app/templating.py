"""Instancia única de Jinja2Templates compartida por toda la aplicación.

Construir Jinja2Templates crea un entorno Jinja completo (carga del loader,
configuración de filtros, autoescape). Hacerlo en cada request es trabajo
desperdiciado; aquí se crea una sola vez al importar el módulo.
"""

from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")
