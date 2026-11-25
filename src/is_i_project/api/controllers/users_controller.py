from __future__ import annotations

from is_i_project.api.utils import (
    error_response,
    get_json_body,
    hash_password,
    login_required,
    serialize_user_detail,
    success_response,
)
from is_i_project.extensions import db
from is_i_project.models import User


def list_users():
    users_rows = db.session.execute(
        db.select(User).order_by(User.id.asc())
    ).scalars().all()
    users = [serialize_user_detail(user) for user in users_rows]
    return success_response({"users": users}, 200)


def get_user(user_id: int):
    user = db.session.get(User, user_id)
    if user is None:
        return error_response("Usuario no encontrado", 404)
    return success_response({"user": serialize_user_detail(user)}, 200)


@login_required
def create_user():
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
        return error_response("Ya existe un usuario con ese email", 409)

    user = User(
        name=name,
        email=email,
        password=hash_password(password),
    )
    db.session.add(user)
    db.session.commit()

    return success_response(
        {
            "message": "Usuario creado exitosamente",
            "user": serialize_user_detail(user),
        },
        201,
    )
