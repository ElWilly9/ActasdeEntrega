from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Assignment, User, Validation
from app.models.user import UserRole
from app.routers.auth import get_current_user
from app.services.pdf import generate_assignment_pdf, generate_validation_pdf

router = APIRouter(tags=["reports"])


def _verificar_acceso(classroom_id: int, user: User) -> None:
    """El admin accede a todo; el profesor solo a las actas de SU salon."""
    if user.rol != UserRole.admin and classroom_id != user.classroom_id:
        raise HTTPException(status_code=403, detail="No autorizado para ver este comprobante")


@router.get("/reports/assignment/{assignment_id}")
def download_assignment_pdf(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    preview: bool = Query(False),
):
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Acta no encontrada")
    _verificar_acceso(assignment.classroom_id, current_user)

    disposition = "inline" if preview else "attachment"
    pdf_bytes = generate_assignment_pdf(assignment_id, db)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"{disposition}; filename=acta_entrega_{assignment_id}.pdf"},
    )


@router.get("/reports/validation/{validation_id}")
def download_validation_pdf(
    validation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    preview: bool = Query(False),
):
    validation = db.query(Validation).filter(Validation.id == validation_id).first()
    if not validation:
        raise HTTPException(status_code=404, detail="Validacion no encontrada")
    _verificar_acceso(validation.assignment.classroom_id, current_user)

    disposition = "inline" if preview else "attachment"
    pdf_bytes = generate_validation_pdf(validation_id, db)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"{disposition}; filename=acta_devolucion_{validation_id}.pdf"},
    )
