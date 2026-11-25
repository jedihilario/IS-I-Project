from flask import Blueprint

from is_i_project.api.controllers import admin_controller

admin_bp = Blueprint("api_admin", __name__, url_prefix="/api/admin")

admin_bp.add_url_rule(
    "/users/<int:user_id>",
    view_func=admin_controller.delete_user,
    methods=["DELETE"],
)
