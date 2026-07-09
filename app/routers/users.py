from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.templating import templates
from app.models import Classroom, User
from app.models.user import UserRole
from app.routers.auth import get_current_user, require_admin
from app.services.auth import hash_password

router = APIRouter(tags=["teachers"])


@router.get("/teachers")
def list_teachers(request: Request, db: Session = Depends(get_db), _=Depends(require_admin)):
    q = request.query_params.get("q", "").strip()
    query = db.query(User).filter(User.rol == UserRole.profesor)
    if q:
        query = query.outerjoin(Classroom).filter(
            User.nombre.ilike(f"%{q}%")
            | User.email.ilike(f"%{q}%")
            | Classroom.nombre.ilike(f"%{q}%")
        ).distinct()
    teachers = query.all()
    return templates.TemplateResponse(request, "teachers.html", {"request": request, "teachers": teachers, "q": q, "msg": request.query_params.get("msg")})


@router.get("/teachers/new")
def new_teacher_form(request: Request, db: Session = Depends(get_db), _=Depends(require_admin)):
    classrooms = db.query(Classroom).all()
    return templates.TemplateResponse(request, "teacher_form.html", {"request": request, "teacher": None, "classrooms": classrooms})


@router.post("/teachers")
def create_teacher(
    request: Request,
    email: str = Form(...),
    nombre: str = Form(...),
    classroom_id: int = Form(None),
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="El email ya esta registrado")

    user = User(
        email=email,
        nombre=nombre,
        password_hash=hash_password("cambio123"),
        rol=UserRole.profesor,
        classroom_id=classroom_id if classroom_id and classroom_id > 0 else None,
    )
    db.add(user)
    db.commit()
    return RedirectResponse(url="/teachers?msg=Profesor creado exitosamente", status_code=302)


@router.get("/teachers/{teacher_id}/edit")
def edit_teacher_form(
    request: Request,
    teacher_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    teacher = db.query(User).filter(User.id == teacher_id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Profesor no encontrado")
    classrooms = db.query(Classroom).all()
    return templates.TemplateResponse(request, "teacher_form.html", {"request": request, "teacher": teacher, "classrooms": classrooms})


@router.post("/teachers/{teacher_id}")
def update_teacher(
    request: Request,
    teacher_id: int,
    email: str = Form(...),
    nombre: str = Form(...),
    classroom_id: int = Form(None),
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    teacher = db.query(User).filter(User.id == teacher_id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Profesor no encontrado")

    existing = db.query(User).filter(User.email == email, User.id != teacher_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="El email ya esta en uso")

    teacher.email = email
    teacher.nombre = nombre
    teacher.classroom_id = classroom_id if classroom_id and classroom_id > 0 else None
    db.commit()
    return RedirectResponse(url="/teachers?msg=Profesor actualizado exitosamente", status_code=302)


@router.post("/teachers/{teacher_id}/delete")
def delete_teacher(
    teacher_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    teacher = db.query(User).filter(User.id == teacher_id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Profesor no encontrado")
    db.delete(teacher)
    db.commit()
    return RedirectResponse(url="/teachers?msg=Profesor eliminado exitosamente", status_code=302)
