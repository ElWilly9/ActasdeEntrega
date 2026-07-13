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
  schemas/         # Pydantic schemas (mostly empty — models used directly)
  templates/       # 17 Jinja2 templates (dashboard, forms, PDF views)
  constants.py     # ACTIVOS_COMUNES dropdown list
  templating.py    # shared Jinja2Templates instance
  tz.py            # local_now() helper (naive datetime, Bogota UTC-5)
seed.py            # test data seeder (drops + recreates all tables)
iniciar.bat        # Windows convenience: starts server + opens browser
render.yaml        # Render.com deployment config (uses PostgreSQL)
```

## Commands

```bash
# Seed test data (drops + recreates all tables)
./venv/Scripts/python seed.py

# Start dev server
./venv/Scripts/python -m uvicorn app.main:app --reload --port 8000

# Production (no --reload)
./venv/Scripts/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# Or double-click iniciar.bat (Windows — starts dev server + opens browser)
```

## Dev quick reference

- **Virtual env:** `venv/` (Windows — always use `./venv/Scripts/python`, not global python)
- **DB auto-creates** on startup via `Base.metadata.create_all(bind=engine)` in `main.py` — no migration step. Alembic is in requirements but **not configured** (no `alembic.ini` or `migrations/` dir)
- **Auto-seed:** `main.py` seeds sample data automatically **only when the DB is empty** (no users). `seed.py` forces a full reseed (drops tables first)
- **Reset DB:** delete `inventario.db`, re-run `seed.py`
- **Test credentials:** admin `admin@escuela.cl` / `admin123`; professors `maria@escuela.cl` / `cambio123`, `juan@escuela.cl` / `cambio123`, `baute@bilingue.edu.co` / `cambio123`
- **New professors** get default password `cambio123` — see `app/routers/users.py:51`
- **No tests, no CI, no linter, no formatter, no type checker** — pytest + pytest-asyncio in `requirements.txt` but unused
- **`.env` settings:** `DATABASE_URL`, `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES` (default 480 min / 8 h)

## Architecture notes

- **Auth middleware** (`JWTAuthBackend` in `app/services/auth.py`) reads JWT from `access_token` cookie, populates `request.user` — no bearer token, no session
- **Route guard pattern:** admin-only routes use `Depends(require_admin)`; professor routes use `Depends(get_current_user)` with inline role checks in templates
- **Two PDF types:** delivery certificate (`/reports/assignment/{id}`) and return validation (`/reports/validation/{id}`). Both use `fpdf2` with latin-1 sanitization (`_s()` helper)
- **Professor access control:** each professor is tied to one `classroom_id`. Professors only see their own classroom's assignments and PDFs (`_verificar_acceso` in `app/routers/reports.py:14`)
- **Validation closes an assignment:** when an admin validates a return, the assignment is marked inactive (`active=False`, `closed_at` set) — see `app/routers/validations.py:71-73`
- **Form encoding (assignment creation):** uses multipart parallel arrays (`descripcion[]`, `cantidad[]`, `serial[]`, `estado[]`, `observacion[]`) via `form.getlist()` — NOT JSON
- **"Otro" protocol:** when `descripcion[]` value is `"__otro__"`, the free-text is read from `descripcion_otro[]` at the same index (`app/routers/assignments.py:112-113`)
- **Validation form naming:** each item field is keyed by `item_{id}_devuelto`, `item_{id}_estado`, `item_{id}_observacion`
- **Common assets** (`ACTIVOS_COMUNES` in `constants.py`) populate a dropdown in the assignment form; user can pick one or select "Otro" for free-text

## Gotchas

- All routes, model names, comments, and UI are in **Spanish** — search for Spanish terms, not English
- `app/templating.py` creates a **single** `Jinja2Templates` instance — import it, do not create another
- PDF text sanitized to latin-1 via `_s()` — non-latin-1 chars get replaced, not crashed
- `local_now()` returns a **naive** datetime (no tzinfo) for SQLite compatibility
- DB connection uses `check_same_thread=False` for SQLite — only relevant in dev; PostgreSQL doesn't need it
- **PostgreSQL migration:** config.py auto-injects `+pg8000` driver when `DATABASE_URL` starts with `postgresql://` — do NOT specify driver manually
- **Render deployment:** production uses PostgreSQL (Render managed DB) via config in `render.yaml`; local dev uses SQLite by default
