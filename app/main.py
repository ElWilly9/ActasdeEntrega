from fastapi import Depends, FastAPI, Request
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from starlette.middleware.authentication import AuthenticationMiddleware

from app.database import engine, get_db
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
