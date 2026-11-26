from __future__ import annotations

from is_i_project.api.utils import (
    ControllerError,
    error_response,
    get_json_body,
    hash_password,
    login_required,
    serialize_user_detail,
    success_response,
)
from is_i_project.extensions import db
from is_i_project.models import User


def get_all_users() -> list[User]:
    return list(
        db.session.execute(db.select(User).order_by(User.id.asc())).scalars().all()
    )


def get_user_record(user_id: int) -> User:
    user = db.session.get(User, user_id)
    if user is None:
        raise ControllerError("Usuario no encontrado", 404)
    return user


def list_users():
    users_rows = get_all_users()
    users = [serialize_user_detail(user) for user in users_rows]
    return success_response({"users": users}, 200)


def get_user(user_id: int):
    try:
        user = get_user_record(user_id)
    except ControllerError as exc:
        return error_response(exc.message, exc.status_code)
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
