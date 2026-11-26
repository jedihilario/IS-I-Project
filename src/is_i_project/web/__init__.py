from __future__ import annotations

import secrets

from flask import Flask, session

from is_i_project.api.utils import get_current_user
from is_i_project.web import views
from is_i_project.web.presenters import build_user_vm, count_unanswered_questions


def _csrf_token() -> str:
    token = session.get("_csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["_csrf_token"] = token
    return token


def register_web(app: Flask) -> None:
    """Registra las vistas web HTML (Jinja2) y las variables globales de plantilla."""

    @app.context_processor
    def inject_globals():
        return {
            "current_user": build_user_vm(get_current_user()),
            "csrf_token": _csrf_token,
            "unanswered_count": count_unanswered_questions(),
        }

    app.add_url_rule("/", endpoint="index", view_func=views.index, methods=["GET"])
    app.add_url_rule("/home", endpoint="home", view_func=views.home, methods=["GET"])
    app.add_url_rule(
        "/preguntas/<int:question_id>",
        endpoint="question_detail",
        view_func=views.question_detail,
        methods=["GET"],
    )
    app.add_url_rule(
        "/preguntas/nueva",
        endpoint="question_new",
        view_func=views.question_new,
        methods=["GET", "POST"],
    )
    app.add_url_rule(
        "/preguntas/<int:question_id>/editar",
        endpoint="question_edit",
        view_func=views.question_edit,
        methods=["GET", "POST"],
    )
    app.add_url_rule(
        "/preguntas/<int:question_id>/eliminar",
        endpoint="question_delete",
        view_func=views.question_delete,
        methods=["GET", "POST"],
    )
    app.add_url_rule(
        "/preguntas/<int:question_id>/responder",
        endpoint="answer_create",
        view_func=views.answer_create,
        methods=["POST"],
    )
    app.add_url_rule(
        "/respuestas/<int:answer_id>/eliminar",
        endpoint="answer_delete",
        view_func=views.answer_delete,
        methods=["GET", "POST"],
    )
    app.add_url_rule(
        "/login", endpoint="login", view_func=views.login, methods=["GET", "POST"]
    )
    app.add_url_rule(
        "/registro",
        endpoint="register",
        view_func=views.register,
        methods=["GET", "POST"],
    )
    app.add_url_rule(
        "/logout", endpoint="logout", view_func=views.logout, methods=["GET", "POST"]
    )
    app.add_url_rule(
        "/usuario/<int:user_id>",
        endpoint="profile",
        view_func=views.profile,
        methods=["GET"],
    )
    app.add_url_rule(
        "/perfil/foto",
        endpoint="profile_photo_upload",
        view_func=views.profile_photo_upload,
        methods=["POST"],
    )
    app.add_url_rule(
        "/categorias",
        endpoint="categories",
        view_func=views.categories,
        methods=["GET"],
    )
    app.add_url_rule(
        "/admin",
        endpoint="admin_dashboard",
        view_func=views.admin_dashboard,
        methods=["GET"],
    )
    app.add_url_rule(
        "/admin/config-ia",
        endpoint="admin_config_ai",
        view_func=views.admin_config_ai,
        methods=["POST"],
    )
