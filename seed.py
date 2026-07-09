"""
Script de datos semilla para el Sistema de Inventario Escolar.
Recrea la base de datos desde cero con datos de ejemplo.
"""
from app.database import SessionLocal, engine
from app.models import Base, Assignment, AssignmentItem, Classroom, User
from app.models.assignment import Condicion
from app.models.user import UserRole
from app.services.auth import hash_password


def seed():
    # Recrear todas las tablas desde cero
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # Salones
        aula101 = Classroom(nombre="Aula 101", codigo="A101")
        aula102 = Classroom(nombre="Aula 102", codigo="A102")
        db.add_all([aula101, aula102])
        db.flush()

        # Usuarios
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

        # Acta de ejemplo para el Aula 101
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

        print("Datos semilla creados exitosamente:")
        print("  - 2 salones (Aula 101, Aula 102)")
        print("  - 3 usuarios (admin, Maria, Juan)")
        print("  - 1 acta de ejemplo con 4 activos")
        print("  - Contrasena admin: admin123")
        print("  - Contrasena profesores: cambio123")

    except Exception as e:
        db.rollback()
        print(f"Error al crear datos semilla: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
