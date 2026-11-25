from flask import Blueprint

from is_i_project.api.controllers import categories_controller

categories_bp = Blueprint("api_categories", __name__, url_prefix="/api/categories")

categories_bp.add_url_rule(
    "", view_func=categories_controller.list_categories, methods=["GET"]
)
categories_bp.add_url_rule(
    "", view_func=categories_controller.create_category, methods=["POST"]
)
categories_bp.add_url_rule(
    "/<int:category_id>", view_func=categories_controller.get_category, methods=["GET"]
)
categories_bp.add_url_rule(
    "/<int:category_id>", view_func=categories_controller.update_category, methods=["PUT"]
)
categories_bp.add_url_rule(
    "/<int:category_id>",
    view_func=categories_controller.delete_category,
    methods=["DELETE"],
)
