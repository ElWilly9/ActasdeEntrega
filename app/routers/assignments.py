from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.constants import ACTIVOS_COMUNES
from app.database import get_db
from app.models import Assignment, AssignmentItem, Classroom, User
from app.models.assignment import Condicion
from app.models.user import UserRole
from app.routers.auth import require_admin
from app.templating import templates
from app.tz import local_now

router = APIRouter(tags=["assignments"])


SORTABLE_COLUMNS = {
    "titulo": Assignment.titulo,
    "salon": Classroom.nombre,
    "profesor": User.nombre,
    "entrega": Assignment.assignment_date,
    "cierre": Assignment.closed_at,
    "estado": Assignment.active,
}


@router.get("/assignments")
def list_assignments(
    request: Request,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
    sort_by: str = Query("created_at"),
    sort_dir: str = Query("desc"),
):
    q = request.query_params.get("q", "").strip()
    query = db.query(Assignment).join(Classroom).outerjoin(User, Assignment.user_id == User.id)
    if q:
        query = query.filter(
            Assignment.titulo.ilike(f"%{q}%") | Classroom.nombre.ilike(f"%{q}%")
        )
    if sort_by not in SORTABLE_COLUMNS:
        sort_by = "created_at"
    if sort_dir not in ("asc", "desc"):
        sort_dir = "desc"
    col = SORTABLE_COLUMNS.get(sort_by, Assignment.created_at)
    order_func = col.asc if sort_dir == "asc" else col.desc
    assignments = query.order_by(order_func()).all()
    return templates.TemplateResponse(request, "assignments.html", {
        "request": request,
        "assignments": assignments,
        "q": q,
        "sort_by": sort_by,
        "sort_dir": sort_dir,
        "msg": request.query_params.get("msg"),
    })


@router.get("/assignments/new")
def new_assignment_form(request: Request, db: Session = Depends(get_db), _=Depends(require_admin)):
    classrooms = db.query(Classroom).order_by(Classroom.nombre).all()
    teachers = db.query(User).filter(User.rol == UserRole.profesor, User.activo == True).order_by(User.nombre).all()
    return templates.TemplateResponse(request, "assignment_form.html", {
        "request": request,
        "classrooms": classrooms,
        "teachers": teachers,
        "activos_comunes": ACTIVOS_COMUNES,
        "condiciones": [c.value for c in Condicion],
    })


@router.post("/assignments")
async def create_assignment(
    request: Request,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    form = await request.form()

    classroom_id = form.get("classroom_id")
    titulo = (form.get("titulo") or "").strip()
    user_id = form.get("user_id")
    if not classroom_id or not titulo:
        raise HTTPException(status_code=400, detail="Salon y titulo son obligatorios")

    classroom = db.query(Classroom).filter(Classroom.id == int(classroom_id)).first()
    if not classroom:
        raise HTTPException(status_code=404, detail="Salon no encontrado")

    # Validate user_id if provided
    profesor_id = None
    if user_id:
        user = db.query(User).filter(User.id == int(user_id), User.rol == UserRole.profesor).first()
        if user:
            profesor_id = user.id

    # Arrays paralelos: cada fila aporta un valor a cada lista (alineados por indice)
    descripciones = form.getlist("descripcion")
    descripciones_otro = form.getlist("descripcion_otro")
    cantidades = form.getlist("cantidad")
    seriales = form.getlist("serial")
    estados = form.getlist("estado")
    observaciones = form.getlist("observacion")

    assignment = Assignment(classroom_id=classroom.id, titulo=titulo, user_id=profesor_id)
    db.add(assignment)
    db.flush()

    items_creados = 0
    for i in range(len(descripciones)):
        desc_sel = (descripciones[i] or "").strip()
        # Si eligio "Otro" se usa el texto libre correspondiente
        if desc_sel == "__otro__":
            desc = (descripciones_otro[i] if i < len(descripciones_otro) else "").strip()
        else:
            desc = desc_sel
        if not desc:
            continue  # fila vacia: se ignora

        try:
            cantidad = int(cantidades[i]) if i < len(cantidades) and cantidades[i] else 1
        except ValueError:
            cantidad = 1
        cantidad = max(1, cantidad)

        estado_val = estados[i] if i < len(estados) else Condicion.bueno.value
        try:
            estado = Condicion(estado_val)
        except ValueError:
            estado = Condicion.bueno

        item = AssignmentItem(
            assignment_id=assignment.id,
            cantidad=cantidad,
            descripcion=desc,
            serial=(seriales[i].strip() or None) if i < len(seriales) else None,
            estado=estado,
            observacion=(observaciones[i].strip() or None) if i < len(observaciones) else None,
        )
        db.add(item)
        items_creados += 1

    if items_creados == 0:
        db.rollback()
        raise HTTPException(status_code=400, detail="El acta debe tener al menos un activo")

    db.commit()
    return RedirectResponse(url=f"/assignments/{assignment.id}?msg=Acta creada exitosamente", status_code=302)


@router.get("/assignments/{assignment_id}")
def assignment_detail(
    request: Request,
    assignment_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Acta no encontrada")
    return templates.TemplateResponse(request, "assignment_detail.html", {
        "request": request,
        "assignment": assignment,
        "activos_comunes": ACTIVOS_COMUNES,
        "condiciones": [c.value for c in Condicion],
        "msg": request.query_params.get("msg"),
    })


@router.post("/assignments/{assignment_id}/items")
async def add_assignment_items(
    assignment_id: int,
    request: Request,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Acta no encontrada")
    if not assignment.active:
        raise HTTPException(status_code=400, detail="No se pueden agregar activos a un acta cerrada")

    form = await request.form()

    descripciones = form.getlist("descripcion")
    descripciones_otro = form.getlist("descripcion_otro")
    cantidades = form.getlist("cantidad")
    seriales = form.getlist("serial")
    estados = form.getlist("estado")
    observaciones = form.getlist("observacion")

    items_creados = 0
    for i in range(len(descripciones)):
        desc_sel = (descripciones[i] or "").strip()
        if desc_sel == "__otro__":
            desc = (descripciones_otro[i] if i < len(descripciones_otro) else "").strip()
        else:
            desc = desc_sel
        if not desc:
            continue

        try:
            cantidad = int(cantidades[i]) if i < len(cantidades) and cantidades[i] else 1
        except ValueError:
            cantidad = 1
        cantidad = max(1, cantidad)

        estado_val = estados[i] if i < len(estados) else Condicion.bueno.value
        try:
            estado = Condicion(estado_val)
        except ValueError:
            estado = Condicion.bueno

        item = AssignmentItem(
            assignment_id=assignment.id,
            cantidad=cantidad,
            descripcion=desc,
            serial=(seriales[i].strip() or None) if i < len(seriales) else None,
            estado=estado,
            observacion=(observaciones[i].strip() or None) if i < len(observaciones) else None,
        )
        db.add(item)
        items_creados += 1

    if items_creados == 0:
        raise HTTPException(status_code=400, detail="Debe agregar al menos un activo")

    db.commit()
    return RedirectResponse(url=f"/assignments/{assignment_id}?msg=Activos agregados exitosamente", status_code=302)


@router.post("/assignments/{assignment_id}/close")
def close_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Acta no encontrada")
    assignment.active = False
    assignment.closed_at = local_now()
    db.commit()
    return RedirectResponse(url=f"/assignments/{assignment_id}?msg=Acta cerrada exitosamente", status_code=302)


@router.get("/api/assignments/last-closed")
def get_last_closed_assignment(
    classroom_id: int = Query(...),
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    """Devuelve la ultima acta cerrada de un salon con sus items."""
    assignment = (
        db.query(Assignment)
        .filter(Assignment.classroom_id == classroom_id, Assignment.active == False)
        .order_by(Assignment.closed_at.desc())
        .first()
    )
    if not assignment:
        return {"assignment": None, "items": []}

    items = [
        {
            "descripcion": item.descripcion,
            "cantidad": item.cantidad,
            "serial": item.serial or "",
            "estado": item.estado.value if item.estado else Condicion.bueno.value,
            "observacion": item.observacion or "",
        }
        for item in assignment.items
    ]

    return {
        "assignment": {
            "id": assignment.id,
            "titulo": assignment.titulo,
            "closed_at": assignment.closed_at.isoformat() if assignment.closed_at else None,
        },
        "items": items,
    }
