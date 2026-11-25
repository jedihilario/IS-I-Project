from __future__ import annotations

from datetime import date

from is_i_project.api.utils import (
    error_response,
    get_current_user,
    get_json_body,
    login_required,
    success_response,
    toggle_vote,
)
from is_i_project.extensions import db
from is_i_project.models import Question, Response


@login_required
def create_answer(question_id: int):
    question = db.session.get(Question, question_id)
    if question is None:
        return error_response("Pregunta no encontrada", 404)

    data = get_json_body()
    if data is None:
        return error_response("Cuerpo JSON inválido o ausente", 400)

    body = (data.get("body") or "").strip()
    if not body:
        return error_response("El campo 'body' es obligatorio", 400)

    user = get_current_user()
    answer = Response(
        body=body,
        post_date=date.today(),
        accepted=False,
        author=user,
        question=question,
    )
    db.session.add(answer)
    db.session.commit()

    return success_response(
        {
            "answer_id": answer.id,
            "message": "Respuesta publicada",
        },
        201,
    )


@login_required
def update_answer(answer_id: int):
    answer = db.session.get(Response, answer_id)
    if answer is None:
        return error_response("Respuesta no encontrada", 404)

    user = get_current_user()
    if answer.author_id != user.id:
        return error_response("No tenés permisos para editar esta respuesta", 403)

    data = get_json_body()
    if data is None:
        return error_response("Cuerpo JSON inválido o ausente", 400)

    body = (data.get("body") or "").strip()
    if not body:
        return error_response("El campo 'body' es obligatorio", 400)

    answer.body = body
    db.session.commit()
    return success_response({"message": "Respuesta actualizada"}, 200)


@login_required
def delete_answer(answer_id: int):
    answer = db.session.get(Response, answer_id)
    if answer is None:
        return error_response("Respuesta no encontrada", 404)

    user = get_current_user()
    if answer.author_id != user.id:
        return error_response("No tenés permisos para eliminar esta respuesta", 403)

    db.session.delete(answer)
    db.session.commit()
    return success_response({"message": "Respuesta eliminada"}, 200)


@login_required
def vote_answer(answer_id: int):
    answer = db.session.get(Response, answer_id)
    if answer is None:
        return error_response("Respuesta no encontrada", 404)

    data = get_json_body()
    if data is None:
        return error_response("Cuerpo JSON inválido o ausente", 400)

    direction = (data.get("direction") or "").strip().lower()
    if direction not in {"up", "down"}:
        return error_response("El campo 'direction' debe ser 'up' o 'down'", 400)

    user = get_current_user()
    new_score, user_vote = toggle_vote(answer, user.id, direction)
    return success_response(
        {
            "new_score": new_score,
            "user_vote": user_vote,
        },
        200,
    )


@login_required
def accept_answer(answer_id: int):
    answer = db.session.get(Response, answer_id)
    if answer is None:
        return error_response("Respuesta no encontrada", 404)

    user = get_current_user()
    if answer.question.author_id != user.id:
        return error_response(
            "Solo el autor de la pregunta puede marcar una respuesta como aceptada",
            403,
        )

    for resp in answer.question.responses:
        resp.accepted = resp.id == answer.id

    db.session.commit()
    return success_response({"accepted_answer_id": answer.id}, 200)
