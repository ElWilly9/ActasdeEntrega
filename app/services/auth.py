from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from starlette.authentication import AuthCredentials, AuthenticationBackend, SimpleUser

from app.config import settings
from app.tz import BOGOTA

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password.encode("utf-8")[:72].decode("utf-8", errors="ignore"))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(BOGOTA) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


class AuthUser(SimpleUser):
    """Usuario autenticado expuesto en request.user para las plantillas."""

    def __init__(self, nombre: str, email: str, rol: str):
        super().__init__(email)
        self.nombre = nombre
        self.email = email
        self.rol = rol


class JWTAuthBackend(AuthenticationBackend):
    """Lee el JWT de la cookie y puebla request.user sin tocar la BD."""

    async def authenticate(self, conn):
        token = conn.cookies.get("access_token")
        if not token:
            return None
        payload = decode_token(token)
        if not payload:
            return None
        nombre = payload.get("nombre") or payload.get("sub", "")
        return AuthCredentials(["authenticated"]), AuthUser(
            nombre=nombre, email=payload.get("sub", ""), rol=payload.get("rol", "")
        )
