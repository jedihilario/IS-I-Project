from __future__ import annotations

from flask import session
from sqlalchemy import func

from is_i_project.api.utils import (
    ControllerError,
    clear_session_user,
    error_response,
    get_current_user,
    get_json_body,
    hash_password,
    serialize_user_detail,
    set_session_user,
    success_response,
    verify_password,
)
from is_i_project.extensions import db
from is_i_project.models import Role, User


def _get_or_create_role(role_name: str) -> Role:
    normalized = role_name.strip().lower()
    if normalized not in {"admin", "usuario"}:
        normalized = "usuario"
    role = db.session.execute(
        db.select(Role).where(func.lower(Role.name) == normalized)
    ).scalar_one_or_none()
    if role is None:
        role = Role(name=normalized)
        db.session.add(role)
        db.session.flush()
    return role


def register_user_record(
    *,
    name: str,
    email: str,
    password: str,
    role_name: str | None = None,
    password_confirm: str | None = None,
    min_password_length: int = 1,
) -> User:
    clean_name = (name or "").strip()
    clean_email = (email or "").strip().lower()
    raw_password = password or ""

    if not clean_name or not clean_email or not raw_password:
        raise ControllerError(
            "Los campos 'name', 'email' y 'password' son obligatorios", 400
        )
    if len(clean_name) > 31:
        raise ControllerError("El nombre no puede superar los 31 caracteres", 400)
    if len(clean_email) > 127 or "@" not in clean_email:
        raise ControllerError("El email no es válido", 400)
    if len(raw_password) < min_password_length:
        raise ControllerError(
            f"La contraseña debe tener al menos {min_password_length} caracteres", 400
        )
    if password_confirm is not None and raw_password != password_confirm:
        raise ControllerError("Las contraseñas no coinciden", 400)

    existing = db.session.execute(
        db.select(User).where(User.email == clean_email)
    ).scalar_one_or_none()
    if existing is not None:
        raise ControllerError("Ya existe un usuario registrado con ese email", 409)

    role_id = _get_or_create_role(role_name).id if role_name is not None else None
    user = User(
        name=clean_name,
        email=clean_email,
        password=hash_password(raw_password),
        role_id=role_id,
    )
    db.session.add(user)
    db.session.commit()

    set_session_user(user)
    return user


def authenticate_user_record(
    *, email: str, password: str, remember_me: bool = False
) -> User:
    clean_email = (email or "").strip().lower()
    raw_password = password or ""

    if not clean_email or not raw_password:
        raise ControllerError("Los campos 'email' y 'password' son obligatorios", 400)

    user = db.session.execute(
        db.select(User).where(User.email == clean_email)
    ).scalar_one_or_none()
    if user is None or not verify_password(user.password, raw_password):
        raise ControllerError("Credenciales inválidas", 401)

    set_session_user(user)
    if remember_me:
        session.permanent = True
    return user


def logout_user_session() -> None:
    clear_session_user()


def register():
    data = get_json_body()
    if data is None:
        return error_response("Cuerpo JSON inválido o ausente", 400)

    try:
        user = register_user_record(
            name=data.get("name") or "",
            email=data.get("email") or "",
            password=data.get("password") or "",
        )
    except ControllerError as exc:
        return error_response(exc.message, exc.status_code)

    return success_response(
        {
            "message": "Usuario registrado exitosamente",
            "user": serialize_user_detail(user),
        },
        201,
    )


def login():
    data = get_json_body()
    if data is None:
        return error_response("Cuerpo JSON inválido o ausente", 400)

    try:
        user = authenticate_user_record(
            email=data.get("email") or "",
            password=data.get("password") or "",
        )
    except ControllerError as exc:
        return error_response(exc.message, exc.status_code)

    return success_response(
        {
            "message": "Sesión iniciada correctamente",
            "user": serialize_user_detail(user),
        },
        200,
    )


def logout():
    logout_user_session()
    return success_response({"message": "Sesión cerrada correctamente"}, 200)


def me():
    user = get_current_user()
    if user is None:
        return error_response("Autenticación requerida", 401)
    return success_response({"user": serialize_user_detail(user)}, 200)
