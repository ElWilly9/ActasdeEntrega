from fastapi import Depends, FastAPI, Request
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from starlette.middleware.authentication import AuthenticationMiddleware

from app.database import SessionLocal, engine, get_db
from app.models import Base
from app.models import Assignment, Classroom, User
from app.models.user import UserRole
from app.routers import assignments, auth, classrooms, reports, users, validations
from app.services.auth import JWTAuthBackend
from app.templating import templates

# Crear todas las tablas (compatible con PostgreSQL y SQLite)
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"[WARN] No se pudieron crear las tablas al iniciar: {e}")

# Auto-seed: si la BD esta vacia (no hay usuarios), siembra datos de prueba
from sqlalchemy.orm import Session
from app.models.assignment import AssignmentItem, Condicion
from app.services.auth import hash_password


def _auto_seed():
    db = SessionLocal()
    try:
        existing = db.query(User).count()
        if existing > 0:
            return

        print("[seed] Base de datos vacia — sembrando datos de prueba...")

        aula101 = Classroom(nombre="Aula 101", codigo="A101")
        aula102 = Classroom(nombre="Aula 102", codigo="A102")
        db.add_all([aula101, aula102])
        db.flush()

        admin = User(
            email="admin@escuela.cl",
            nombre="Administrador",
            password_hash=hash_password("admin123"),
            rol=UserRole.admin,
        )
        maria = User(
            email="maria@escuela.cl",
            nombre="Maria Lopez",
            password_hash=hash_password("cambio123"),
            rol=UserRole.profesor,
            classroom_id=aula101.id,
        )
        juan = User(
            email="juan@escuela.cl",
            nombre="Juan Perez",
            password_hash=hash_password("cambio123"),
            rol=UserRole.profesor,
            classroom_id=aula102.id,
        )
        db.add_all([admin, maria, juan])
        db.flush()

        acta = Assignment(classroom_id=aula101.id, titulo="Entrega ano escolar 2025-2026")
        db.add(acta)
        db.flush()

        db.add_all([
            AssignmentItem(assignment_id=acta.id, cantidad=1, descripcion="Televisor",
                           serial="TV-001", estado=Condicion.bueno, observacion="Marca SONY"),
            AssignmentItem(assignment_id=acta.id, cantidad=1, descripcion="Escritorio",
                           serial=None, estado=Condicion.regular, observacion="Esta floja una pata"),
            AssignmentItem(assignment_id=acta.id, cantidad=23, descripcion="Silla",
                           serial=None, estado=Condicion.bueno, observacion="Faltan tapones a algunas"),
            AssignmentItem(assignment_id=acta.id, cantidad=4, descripcion="Abanico",
                           serial=None, estado=Condicion.malo, observacion="Solo funciona uno"),
        ])
        db.commit()
        print("[seed] Datos de prueba creados: admin/admin123, profe maria/cambio123, profe juan/cambio123")
    except Exception as e:
        db.rollback()
        print(f"[seed] Error al sembrar datos: {e}")
    finally:
        db.close()


_auto_seed()

app = FastAPI(title="Sistema de Inventario Escolar")

# Middleware que puebla request.user desde el JWT de la cookie
app.add_middleware(AuthenticationMiddleware, backend=JWTAuthBackend())

# Montar archivos estaticos
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Incluir routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(classrooms.router)
app.include_router(assignments.router)
app.include_router(validations.router)
app.include_router(reports.router)


@app.get("/dashboard")
def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_user),
):
    # Vista del profesor: solo las actas de SU salon, sin datos administrativos
    if current_user.rol == UserRole.profesor:
        if current_user.classroom_id:
            assignments = (
                db.query(Assignment)
                .filter(Assignment.classroom_id == current_user.classroom_id)
                .order_by(Assignment.created_at.desc())
                .all()
            )
        else:
            assignments = []
        return templates.TemplateResponse(request, "mis_actas.html", {
            "request": request,
            "assignments": assignments,
        })

    total_teachers = db.query(User).filter(User.rol == UserRole.profesor, User.activo == True).count()
    total_classrooms = db.query(Classroom).count()
    total_assignments = db.query(Assignment).filter(Assignment.active == True).count()

    # Busqueda de profesores por nombre o salon
    q = request.query_params.get("q", "")
    teachers_query = db.query(User).filter(User.rol == UserRole.profesor)
    if q:
        teachers_query = teachers_query.join(Classroom, isouter=True).filter(
            User.nombre.ilike(f"%{q}%") | Classroom.nombre.ilike(f"%{q}%")
        ).distinct()
    teachers = teachers_query.all()

    return templates.TemplateResponse(request, "dashboard.html", {
        "request": request,
        "total_teachers": total_teachers,
        "total_classrooms": total_classrooms,
        "total_assignments": total_assignments,
        "teachers": teachers,
        "q": q,
    })


# Manejadores de errores
@app.exception_handler(404)
async def not_found(request: Request, exc):
    return templates.TemplateResponse(request, "404.html", {"request": request}, status_code=404)


@app.exception_handler(403)
async def forbidden(request: Request, exc):
    return templates.TemplateResponse(request, "403.html", {"request": request}, status_code=403)


@app.exception_handler(500)
async def server_error(request: Request, exc):
    return templates.TemplateResponse(request, "500.html", {"request": request}, status_code=500)
