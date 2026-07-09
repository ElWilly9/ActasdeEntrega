# Guía de Inicio — Sistema de Inventario Escolar

Aplicación web para gestionar el inventario escolar: salones, profesores, activos,
actas de entrega y validación de devoluciones con comprobante en PDF.

Pensada para uso **administrativo** al inicio y fin del año académico.

---

## Credenciales

| Rol | Email | Contraseña |
|-----|-------|------------|
| **Admin** | `admin@escuela.cl` | `admin123` |
| Profesor | `maria@escuela.cl` | `cambio123` |
| Profesor | `juan@escuela.cl` | `cambio123` |

> El **admin** gestiona todo (salones, profesores, activos, asignaciones, validaciones).
> El **profesor** solo ve y descarga sus propios comprobantes.

---

## Cómo ejecutar

Desde la carpeta del proyecto (`C:\Users\Willy\Documents\Work\test`):

### 1. (Solo la primera vez) Cargar datos de prueba

```bash
./venv/Scripts/python seed.py
```

Si los datos ya existen, mostrará *"Los datos semilla ya existen. Omitiendo..."* — es normal,
no los duplica.

### 2. Arrancar el servidor

```bash
./venv/Scripts/python -m uvicorn app.main:app --reload --port 8000
```

### 3. Abrir en el navegador

```
http://localhost:8000
```

Te redirige al login. Entra con el admin.

### 4. Detener el servidor

`Ctrl + C` en la terminal.

---

## Notas

- **`--reload`** reinicia el servidor automáticamente cuando editas código (útil al desarrollar).
  Para uso normal puedes quitarlo.
- La base de datos es el archivo **`inventario.db`** (SQLite). Para empezar de cero, bórralo y
  vuelve a correr `seed.py`.
- Todo corre dentro del entorno virtual `venv/` ya creado; por eso se invoca
  `./venv/Scripts/python` y no el Python global del sistema.
- Si el puerto 8000 está ocupado, cambia `--port 8000` por otro (ej. `--port 8001`) y ajusta la URL.

---

## Flujo de trabajo típico (admin)

1. **Inicio de año:** crear/revisar salones y profesores (cada profesor se asocia a un salón).
2. **Entrega:** crear un *Acta de Entrega* para un salón. Le pones un **título**
   (ej. "Entrega año escolar 2025-2026") y agregas los activos uno a uno: por cada fila eliges
   el activo de un **desplegable** (o "Otro..." para escribir uno nuevo) e indicas
   **cantidad, serial, condición (Malo/Regular/Bueno) y observación**. Descargas el PDF para firma.
3. **Fin de año:** *Validar Devolución* — por cada activo marcas si fue devuelto, su condición
   al volver y una observación. Al validar, el acta se **cierra** (queda registrada la fecha de cierre).
   Descargas el comprobante de devolución.

El profesor, al entrar, ve directamente las actas **de su salón** y puede descargar sus
comprobantes (entrega y devolución), pero no puede editar nada.

> Nota: no hay sección de "Inventario" global. La condición de cada activo se registra
> dentro de cada acta, porque varía según el salón y el momento de la entrega/devolución.

---

## Stack técnico

- **Backend:** FastAPI + SQLAlchemy (Python 3.14)
- **Base de datos:** SQLite (`inventario.db`); cambiable a PostgreSQL vía `DATABASE_URL` en `.env`
- **Plantillas:** Jinja2 + Tailwind CSS (CDN) + iconos Lucide
- **Autenticación:** JWT en cookie httponly + control de acceso por rol (admin / profesor)
- **PDF:** fpdf2
