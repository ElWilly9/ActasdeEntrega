# AGENTS.md — Sistema de Inventario Escolar

## Stack

- **Backend:** FastAPI + SQLAlchemy (sync), Python 3.14
- **DB:** SQLite (`inventario.db`) — swap to PostgreSQL by changing `DATABASE_URL` in `.env`
- **Templates:** Jinja2 + Tailwind CSS (CDN) + Lucide icons
- **Auth:** JWT in httponly cookie; roles `admin` / `profesor`
- **PDF:** fpdf2 (latin-1 font encoding)
- **Timezone:** Colombia UTC-5 (`app/tz.py`)
- **Locale:** Spanish (es-ES) — all UI, routes, and code comments are in Spanish

## Project layout

```
app/
  main.py          # FastAPI entrypoint, mounts routers, auto-creates tables
  config.py        # pydantic-settings from .env
  database.py      # sync SQLAlchemy engine + SessionLocal
  models/          # SQLAlchemy models (User, Classroom, Assignment, etc.)
  routers/         # auth, users, classrooms, assignments, validations, reports
  services/        # auth (JWT/hash), pdf (fpdf2 generation)
  templates/       # 17 Jinja2 templates (dashboard, forms, PDF views)
  constants.py     # ACTIVOS_COMUNES dropdown list
  templating.py    # shared Jinja2Templates instance
  tz.py            # local_now() helper (naive datetime, Bogota UTC-5)
seed.py            # test data seeder (drops + recreates all tables)
```

## Commands

```bash
# Seed test data (first time or after deleting inventario.db)
./venv/Scripts/python seed.py

# Start dev server
./venv/Scripts/python -m uvicorn app.main:app --reload --port 8000

# Start production (no --reload)
./venv/Scripts/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Dev quick reference

- **Virtual env:** `venv/` (Windows — use `./venv/Scripts/python`, not global python)
- **DB auto-creates** on startup via `Base.metadata.create_all(bind=engine)` in `main.py` — no migration step needed
- **Reset DB:** delete `inventario.db`, re-run `seed.py`
- **Test credentials:** admin `admin@escuela.cl` / `admin123`; professors `maria@escuela.cl` / `cambio123`, `juan@escuela.cl` / `cambio123`
- **No tests exist yet** — pytest + pytest-asyncio are in `requirements.txt` but unused. No CI, no linter, no formatter, no type checker config present.
- **`.env` settings:** `DATABASE_URL`, `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES` (default 480 min / 8 h)

## Architecture notes

- **Auth middleware** (`JWTAuthBackend` in `app/services/auth.py`) reads JWT from `access_token` cookie, populates `request.user` — no bearer token, no session
- **Route guard pattern:** admin-only routes use `Depends(require_admin)`; professor routes use `Depends(get_current_user)` with inline role checks in templates
- **Two PDF types:** delivery certificate (`/reports/assignment/{id}`) and return validation (`/reports/validation/{id}`). Both use `fpdf2` with latin-1 sanitization (`_s()` helper)
- **Professor access control:** each professor is tied to one `classroom_id`. Professors only see their own classroom's assignments and PDFs
- **Validation closes an assignment:** when an admin validates a return, the assignment is marked inactive (`active=False`, `closed_at` set)
- **Form encoding:** assignment creation uses multipart parallel arrays (`descripcion[]`, `cantidad[]`, etc.) — NOT JSON. Validation form uses `item_{id}_*` naming
- **Common assets** (`ACTIVOS_COMUNES` in `constants.py`) populate a dropdown in the assignment form; user can pick one or select "Otro" for free-text

## Gotchas

- All routes, model names, comments, and UI are in **Spanish** — search for Spanish terms, not English
- `app/templating.py` creates a **single** `Jinja2Templates` instance — import it, do not create another
- PDF text sanitized to latin-1 via `_s()` — non-latin-1 chars get replaced, not crashed
- `local_now()` returns a **naive** datetime (no tzinfo) for SQLite compatibility
- DB connection uses `check_same_thread=False` for SQLite — relevant only in dev; PostgreSQL doesn't need it
