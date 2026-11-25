from flask import Blueprint

from is_i_project.api.controllers import users_controller

users_bp = Blueprint("api_users", __name__, url_prefix="/api/users")

users_bp.add_url_rule("", view_func=users_controller.list_users, methods=["GET"])
users_bp.add_url_rule("", view_func=users_controller.create_user, methods=["POST"])
users_bp.add_url_rule("/<int:user_id>", view_func=users_controller.get_user, methods=["GET"])
