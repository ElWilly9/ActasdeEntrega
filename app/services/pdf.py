from fpdf import FPDF
from sqlalchemy.orm import Session

from app.models import Assignment, Validation


def _s(text) -> str:
    """Sanea texto a latin-1 (fuente core de fpdf2). Conserva acentos y enie;
    reemplaza solo caracteres realmente fuera de latin-1 para no romper el PDF."""
    return str(text).encode("latin-1", errors="replace").decode("latin-1")


def _estado_str(estado) -> str:
    if estado is None:
        return "-"
    return estado.value if hasattr(estado, "value") else str(estado)


def _encabezado(pdf: FPDF, titulo_doc: str, assignment: Assignment) -> None:
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Fundacion Colegio Bilingue de Valledupar", ln=True, align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, "Sistema de Inventario Escolar", ln=True, align="C")
    pdf.ln(3)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 9, titulo_doc, ln=True, align="C")
    pdf.ln(2)

    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, _s(f"Titulo: {assignment.titulo}"), ln=True)
    classroom = assignment.classroom
    if classroom:
        pdf.cell(0, 7, _s(f"Salon: {classroom.nombre} ({classroom.codigo})"), ln=True)
    fecha = assignment.assignment_date.strftime("%d/%m/%Y %H:%M") if assignment.assignment_date else "-"
    pdf.cell(0, 7, _s(f"Fecha de entrega: {fecha}"), ln=True)
    pdf.ln(3)


def _firmas(pdf: FPDF) -> None:
    pdf.ln(15)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(90, 7, "____________________________", ln=False)
    pdf.cell(10, 7, "", ln=False)
    pdf.cell(90, 7, "____________________________", ln=True)
    pdf.cell(90, 7, "Administrador", ln=False)
    pdf.cell(10, 7, "", ln=False)
    pdf.cell(90, 7, "Profesor", ln=True)


def generate_assignment_pdf(assignment_id: int, db: Session) -> bytes:
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        return b""

    pdf = FPDF()
    pdf.add_page()
    _encabezado(pdf, "ACTA DE ENTREGA", assignment)

    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, _s("A continuacion se relacionan los objetos que seran entregados al profesor para su uso en el salon de clases."), ln=True)
    pdf.ln(3)

    # Columnas: Cantidad | Descripcion | Serial | Estado | Observacion
    pdf.set_font("Helvetica", "", 9)
    with pdf.table(col_widths=(12, 32, 22, 16, 30), text_align="LEFT") as table:
        table.row(["Cant.", "Descripcion", "Serial", "Estado", "Observacion"])
        for item in assignment.items:
            table.row([
                str(item.cantidad),
                _s(item.descripcion),
                _s(item.serial or "-"),
                _estado_str(item.estado),
                _s(item.observacion or "-"),
            ])

    _firmas(pdf)
    return bytes(pdf.output())


def generate_validation_pdf(validation_id: int, db: Session) -> bytes:
    validation = db.query(Validation).filter(Validation.id == validation_id).first()
    if not validation:
        return b""

    assignment = validation.assignment

    pdf = FPDF()
    pdf.add_page()
    _encabezado(pdf, "ACTA DE DEVOLUCION", assignment)

    fecha_v = validation.validation_date.strftime("%d/%m/%Y %H:%M") if validation.validation_date else "-"
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, _s(f"Fecha de devolucion: {fecha_v}"), ln=True)
    if validation.admin_notes:
        pdf.cell(0, 7, _s(f"Notas: {validation.admin_notes}"), ln=True)
    pdf.ln(3)

    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, _s("A continuacion se relacionan los objetos que han sido devueltos por el profesor."), ln=True)
    pdf.ln(3)

    # Columnas: Cantidad | Descripcion | Serial | Devuelto | Estado | Observacion
    pdf.set_font("Helvetica", "", 9)
    with pdf.table(col_widths=(10, 28, 20, 14, 14, 28), text_align="LEFT") as table:
        table.row(["Cant.", "Descripcion", "Serial", "Devuelto", "Estado", "Observacion"])
        for item in validation.items:
            ai = item.assignment_item
            table.row([
                str(ai.cantidad) if ai else "-",
                _s(ai.descripcion) if ai else "-",
                _s(ai.serial) if ai and ai.serial else "-",
                "Si" if item.devuelto else "No",
                _estado_str(item.estado),
                _s(item.observacion or "-"),
            ])

    _firmas(pdf)
    return bytes(pdf.output())
