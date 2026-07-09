from datetime import timedelta

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse, Response
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.templating import templates
from app.models import User
from app.services.auth import create_token, hash_password, verify_password

router = APIRouter(tags=["auth"])


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    from app.services.auth import decode_token
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    user = db.query(User).filter(User.email == payload.get("sub")).first()
    if not user or not user.activo:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.rol.value != "admin":
        raise HTTPException(status_code=403, detail="Se requieren permisos de administrador")
    return user


@router.get("/login")
def login_form(request: Request):
    token = request.cookies.get("access_token")
    if token:
        from app.services.auth import decode_token
        payload = decode_token(token)
        if payload:
            return RedirectResponse(url="/dashboard", status_code=302)
    from fastapi.responses import HTMLResponse
    return templates.TemplateResponse(request, "login.html", {"request": request, "error": None})


@router.post("/login")
def login_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(request, "login.html", {"request": request, "error": "Email o contrasena incorrectos"}, status_code=401)

    access_token = create_token(
        data={"sub": user.email, "rol": user.rol.value, "nombre": user.nombre},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    resp = RedirectResponse(url="/dashboard", status_code=302)
    resp.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
    )
    return resp


@router.get("/logout")
def logout():
    resp = RedirectResponse(url="/login", status_code=302)
    resp.delete_cookie("access_token")
    return resp


@router.get("/")
def root(request: Request):
    token = request.cookies.get("access_token")
    if token:
        from app.services.auth import decode_token
        payload = decode_token(token)
        if payload:
            return RedirectResponse(url="/dashboard", status_code=302)
    return RedirectResponse(url="/login", status_code=302)
