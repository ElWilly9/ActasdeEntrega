"""Utilidad de zona horaria centralizada."""
from datetime import datetime, timezone, timedelta

# Colombia: UTC-5 sin horario de verano
BOGOTA = timezone(timedelta(hours=-5))


def local_now() -> datetime:
    """Retorna la fecha/hora actual en zona horaria de Bogota (naive para compatibilidad con SQLite)."""
    return datetime.now(BOGOTA).replace(tzinfo=None)
