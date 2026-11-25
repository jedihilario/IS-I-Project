from __future__ import annotations

from flask import Flask, request
from werkzeug.exceptions import HTTPException

from is_i_project.api.routes import ALL_API_BLUEPRINTS
from is_i_project.api.utils import error_response


def register_api(app: Flask) -> None:
    """Registra todos los Blueprints de la REST API y manejadores de error JSON."""
    for blueprint in ALL_API_BLUEPRINTS:
        app.register_blueprint(blueprint)

    @app.errorhandler(HTTPException)
    def handle_http_exception(exc: HTTPException):
        if request.path.startswith("/api"):
            return error_response(exc.description or exc.name, exc.code or 500)
        return exc

    @app.errorhandler(Exception)
    def handle_unexpected_exception(exc: Exception):
        if request.path.startswith("/api"):
            return error_response("Error interno del servidor", 500)
        raise exc
