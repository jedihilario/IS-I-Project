from __future__ import annotations

from is_i_project.api.utils import (
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
from is_i_project.models import User


def register():
    data = get_json_body()
    if data is None:
        return error_response("Cuerpo JSON inválido o ausente", 400)

    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not name or not email or not password:
        return error_response(
            "Los campos 'name', 'email' y 'password' son obligatorios", 400
        )
    if len(name) > 31:
        return error_response("El nombre no puede superar los 31 caracteres", 400)
    if len(email) > 127 or "@" not in email:
        return error_response("El email no es válido", 400)

    existing = db.session.execute(
        db.select(User).where(User.email == email)
    ).scalar_one_or_none()
    if existing is not None:
        return error_response("Ya existe un usuario registrado con ese email", 409)

    user = User(
        name=name,
        email=email,
        password=hash_password(password),
    )
    db.session.add(user)
    db.session.commit()

    set_session_user(user)
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

    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return error_response("Los campos 'email' y 'password' son obligatorios", 400)

    user = db.session.execute(
        db.select(User).where(User.email == email)
    ).scalar_one_or_none()
    if user is None or not verify_password(user.password, password):
        return error_response("Credenciales inválidas", 401)

    set_session_user(user)
    return success_response(
        {
            "message": "Sesión iniciada correctamente",
            "user": serialize_user_detail(user),
        },
        200,
    )


def logout():
    clear_session_user()
    return success_response({"message": "Sesión cerrada correctamente"}, 200)


def me():
    user = get_current_user()
    if user is None:
        return error_response("Autenticación requerida", 401)
    return success_response({"user": serialize_user_detail(user)}, 200)
