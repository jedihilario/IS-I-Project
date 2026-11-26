from __future__ import annotations

from flask import current_app

from is_i_project.api.utils import (
    clear_session_user,
    error_response,
    get_current_user,
    login_required,
    success_response,
)
from is_i_project.extensions import db
from is_i_project.models import AI_Author, User

PROVIDER_TO_MODEL = {
    "openai": "GPT-4o",
    "gemini": "Gemini",
    "local": "Local LLM",
}


def update_ai_config_record(
    *,
    provider: str,
    hours_threshold: int,
    timeout: int,
    enabled: bool,
) -> dict[str, object]:
    normalized_provider = (provider or "openai").strip().lower()
    if normalized_provider not in PROVIDER_TO_MODEL:
        normalized_provider = "openai"

    clamped_hours = max(1, min(720, hours_threshold))
    clamped_timeout = max(5, min(300, timeout))

    ai_author = (
        db.session.execute(db.select(AI_Author).order_by(AI_Author.id.asc()))
        .scalars()
        .first()
    )
    if ai_author is None:
        ai_author = AI_Author(
            modelName=PROVIDER_TO_MODEL[normalized_provider],
            timeout=clamped_timeout,
        )
        db.session.add(ai_author)
    else:
        ai_author.modelName = PROVIDER_TO_MODEL[normalized_provider]
        ai_author.timeout = clamped_timeout
    db.session.commit()

    config_data: dict[str, object] = {
        "provider": normalized_provider,
        "hours_threshold": clamped_hours,
        "timeout": clamped_timeout,
        "enabled": bool(enabled),
    }
    current_app.config["AI_CONFIG"] = config_data
    return config_data


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
