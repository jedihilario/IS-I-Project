from is_i_project.api.routes.admin_routes import admin_bp
from is_i_project.api.routes.answers_routes import answers_bp
from is_i_project.api.routes.auth_routes import auth_bp
from is_i_project.api.routes.categories_routes import categories_bp
from is_i_project.api.routes.questions_routes import questions_bp
from is_i_project.api.routes.tags_routes import tags_bp
from is_i_project.api.routes.users_routes import users_bp

ALL_API_BLUEPRINTS = (
    auth_bp,
    questions_bp,
    answers_bp,
    categories_bp,
    tags_bp,
    users_bp,
    admin_bp,
)

__all__ = [
    "ALL_API_BLUEPRINTS",
    "admin_bp",
    "answers_bp",
    "auth_bp",
    "categories_bp",
    "questions_bp",
    "tags_bp",
    "users_bp",
]
