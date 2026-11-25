from flask import Blueprint

from is_i_project.api.controllers import questions_controller

questions_bp = Blueprint("api_questions", __name__, url_prefix="/api/questions")

questions_bp.add_url_rule("", view_func=questions_controller.list_questions, methods=["GET"])
questions_bp.add_url_rule("", view_func=questions_controller.create_question, methods=["POST"])
questions_bp.add_url_rule(
    "/<int:question_id>", view_func=questions_controller.get_question, methods=["GET"]
)
questions_bp.add_url_rule(
    "/<int:question_id>", view_func=questions_controller.update_question, methods=["PUT"]
)
questions_bp.add_url_rule(
    "/<int:question_id>", view_func=questions_controller.delete_question, methods=["DELETE"]
)
questions_bp.add_url_rule(
    "/<int:question_id>/vote",
    view_func=questions_controller.vote_question,
    methods=["POST"],
)
