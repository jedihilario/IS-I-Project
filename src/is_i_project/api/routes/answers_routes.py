from flask import Blueprint

from is_i_project.api.controllers import answers_controller

answers_bp = Blueprint("api_answers", __name__, url_prefix="/api")

answers_bp.add_url_rule(
    "/questions/<int:question_id>/answers",
    view_func=answers_controller.create_answer,
    methods=["POST"],
)
answers_bp.add_url_rule(
    "/answers/<int:answer_id>",
    view_func=answers_controller.update_answer,
    methods=["PUT"],
)
answers_bp.add_url_rule(
    "/answers/<int:answer_id>",
    view_func=answers_controller.delete_answer,
    methods=["DELETE"],
)
answers_bp.add_url_rule(
    "/answers/<int:answer_id>/vote",
    view_func=answers_controller.vote_answer,
    methods=["POST"],
)
answers_bp.add_url_rule(
    "/answers/<int:answer_id>/accept",
    view_func=answers_controller.accept_answer,
    methods=["POST"],
)
