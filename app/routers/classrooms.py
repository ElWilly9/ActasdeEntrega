from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.templating import templates
from app.models import Classroom
from app.routers.auth import require_admin

router = APIRouter(tags=["classrooms"])


@router.get("/classrooms")
def list_classrooms(request: Request, db: Session = Depends(get_db), _=Depends(require_admin)):
    q = request.query_params.get("q", "").strip()
    query = db.query(Classroom)
    if q:
        query = query.filter(
            Classroom.nombre.ilike(f"%{q}%") | Classroom.codigo.ilike(f"%{q}%")
        )
    classrooms = query.all()
    return templates.TemplateResponse(request, "classrooms.html", {"request": request, "classrooms": classrooms, "q": q, "msg": request.query_params.get("msg")})


@router.get("/classrooms/new")
def new_classroom_form(request: Request, _=Depends(require_admin)):
    return templates.TemplateResponse(request, "classroom_form.html", {"request": request, "classroom": None})


@router.post("/classrooms")
def create_classroom(
    nombre: str = Form(...),
    codigo: str = Form(...),
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    existing = db.query(Classroom).filter(Classroom.codigo == codigo).first()
    if existing:
        raise HTTPException(status_code=400, detail="El codigo de salon ya existe")
    classroom = Classroom(nombre=nombre, codigo=codigo)
    db.add(classroom)
    db.commit()
    return RedirectResponse(url="/classrooms?msg=Salon creado exitosamente", status_code=302)


@router.get("/classrooms/{classroom_id}/edit")
def edit_classroom_form(
    request: Request,
    classroom_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    classroom = db.query(Classroom).filter(Classroom.id == classroom_id).first()
    if not classroom:
        raise HTTPException(status_code=404, detail="Salon no encontrado")
    return templates.TemplateResponse(request, "classroom_form.html", {"request": request, "classroom": classroom})


@router.post("/classrooms/{classroom_id}")
def update_classroom(
    classroom_id: int,
    nombre: str = Form(...),
    codigo: str = Form(...),
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    classroom = db.query(Classroom).filter(Classroom.id == classroom_id).first()
    if not classroom:
        raise HTTPException(status_code=404, detail="Salon no encontrado")
    existing = db.query(Classroom).filter(Classroom.codigo == codigo, Classroom.id != classroom_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="El codigo de salon ya existe")
    classroom.nombre = nombre
    classroom.codigo = codigo
    db.commit()
    return RedirectResponse(url="/classrooms?msg=Salon actualizado exitosamente", status_code=302)


@router.post("/classrooms/{classroom_id}/delete")
def delete_classroom(
    classroom_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    classroom = db.query(Classroom).filter(Classroom.id == classroom_id).first()
    if not classroom:
        raise HTTPException(status_code=404, detail="Salon no encontrado")
    db.delete(classroom)
    db.commit()
    return RedirectResponse(url="/classrooms?msg=Salon eliminado exitosamente", status_code=302)
