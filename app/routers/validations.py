from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Assignment, Validation, ValidationItem
from app.models.assignment import Condicion
from app.routers.auth import require_admin
from app.templating import templates
from app.tz import local_now

router = APIRouter(tags=["validations"])


@router.get("/assignments/{assignment_id}/validate")
def validate_form(
    request: Request,
    assignment_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Acta no encontrada")
    return templates.TemplateResponse(request, "validation.html", {
        "request": request,
        "assignment": assignment,
        "condiciones": [c.value for c in Condicion],
    })


@router.post("/assignments/{assignment_id}/validate")
async def create_validation(
    request: Request,
    assignment_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Acta no encontrada")

    form = await request.form()

    validation = Validation(assignment_id=assignment_id, admin_notes=(form.get("admin_notes") or "").strip() or None)
    db.add(validation)
    db.flush()

    # Por cada item del acta se registra: devuelto (SI/NO), estado y observacion
    for item in assignment.items:
        devuelto = form.get(f"item_{item.id}_devuelto") == "on"

        estado = None
        estado_val = form.get(f"item_{item.id}_estado")
        if estado_val:
            try:
                estado = Condicion(estado_val)
            except ValueError:
                estado = None

        notes = (form.get(f"item_{item.id}_observacion") or "").strip() or None

        db.add(ValidationItem(
            validation_id=validation.id,
            assignment_item_id=item.id,
            devuelto=devuelto,
            estado=estado,
            observacion=notes,
        ))

    # Cerrar el acta al validar la devolucion
    assignment.active = False
    assignment.closed_at = local_now()
    db.commit()

    return RedirectResponse(url=f"/validations/{validation.id}?msg=Validacion completada exitosamente", status_code=302)


@router.get("/validations")
def list_validations(request: Request, db: Session = Depends(get_db), _=Depends(require_admin)):
    validations = db.query(Validation).order_by(Validation.created_at.desc()).all()
    return templates.TemplateResponse(request, "validations_list.html", {
        "request": request,
        "validations": validations,
        "msg": request.query_params.get("msg"),
    })


@router.get("/validations/{validation_id}")
def validation_detail(
    request: Request,
    validation_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    validation = db.query(Validation).filter(Validation.id == validation_id).first()
    if not validation:
        raise HTTPException(status_code=404, detail="Validacion no encontrada")
    return templates.TemplateResponse(request, "validation_detail.html", {
        "request": request,
        "validation": validation,
    })
