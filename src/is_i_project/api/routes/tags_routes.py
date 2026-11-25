from flask import Blueprint

from is_i_project.api.controllers import tags_controller

tags_bp = Blueprint("api_tags", __name__, url_prefix="/api/tags")

tags_bp.add_url_rule("", view_func=tags_controller.list_tags, methods=["GET"])
tags_bp.add_url_rule("", view_func=tags_controller.create_tag, methods=["POST"])
tags_bp.add_url_rule("/<int:tag_id>", view_func=tags_controller.get_tag, methods=["GET"])
tags_bp.add_url_rule("/<int:tag_id>", view_func=tags_controller.update_tag, methods=["PUT"])
tags_bp.add_url_rule(
    "/<int:tag_id>", view_func=tags_controller.delete_tag, methods=["DELETE"]
)
