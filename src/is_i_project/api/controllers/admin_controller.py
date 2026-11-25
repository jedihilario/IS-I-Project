from __future__ import annotations

from is_i_project.api.utils import (
    clear_session_user,
    error_response,
    get_current_user,
    login_required,
    success_response,
)
from is_i_project.extensions import db
from is_i_project.models import User


@login_required
def delete_user(user_id: int):
    user = db.session.get(User, user_id)
    if user is None:
        return error_response("Usuario no encontrado", 404)

    current_user = get_current_user()
    is_self = current_user is not None and current_user.id == user.id

    db.session.delete(user)
    db.session.commit()

    if is_self:
        clear_session_user()

    return success_response({"message": "Usuario eliminado"}, 200)
