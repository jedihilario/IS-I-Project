from __future__ import annotations

import math
from datetime import date

from flask import request
from sqlalchemy import func, or_

from is_i_project.api.utils import (
    error_response,
    get_current_user,
    get_current_user_id,
    get_json_body,
    get_post_score,
    login_required,
    serialize_question_detail,
    serialize_question_summary,
    success_response,
    toggle_vote,
)
from is_i_project.extensions import db
from is_i_project.models import Author, Category, Question, Response, Tag
from is_i_project.models.types import Author_Type


def _resolve_category(data: dict) -> tuple[Category | None, tuple | None]:
    if "category_id" in data and data["category_id"] is not None:
        cat_id = data["category_id"]
        if not isinstance(cat_id, int):
            return None, error_response("'category_id' debe ser un entero", 400)
        cat = db.session.get(Category, cat_id)
        if cat is None:
            return None, error_response("Categoría no encontrada", 404)
        return cat, None

    if "category" in data and data["category"] is not None:
        cat_name = str(data["category"]).strip()
        if not cat_name:
            return None, None
        if len(cat_name) > 63:
            return None, error_response(
                "El nombre de la categoría no puede superar los 63 caracteres", 400
            )
        cat = db.session.execute(
            db.select(Category).where(func.lower(Category.name) == cat_name.lower())
        ).scalar_one_or_none()
        if cat is None:
            cat = Category(name=cat_name)
            db.session.add(cat)
            db.session.flush()
        return cat, None

    return None, None


def _resolve_tags(raw_tags) -> tuple[list[Tag] | None, tuple | None]:
    if raw_tags is None:
        return [], None
    if isinstance(raw_tags, str):
        tag_names = [t.strip().lower() for t in raw_tags.split(",") if t.strip()]
    elif isinstance(raw_tags, list):
        tag_names = [str(t).strip().lower() for t in raw_tags if str(t).strip()]
    else:
        return None, error_response("'tags' debe ser una lista de strings", 400)

    tags: list[Tag] = []
    for name in dict.fromkeys(tag_names):
        if len(name) > 63:
            return None, error_response(
                f"El tag '{name}' supera los 63 caracteres", 400
            )
        tag = db.session.execute(
            db.select(Tag).where(func.lower(Tag.name) == name)
        ).scalar_one_or_none()
        if tag is None:
            tag = Tag(name=name)
            db.session.add(tag)
            db.session.flush()
        tags.append(tag)

    return tags, None


def list_questions():
    category_filter = (request.args.get("category") or "").strip()
    tag_filter = (request.args.get("tag") or "").strip()
    search_query = (request.args.get("q") or "").strip()
    feed_filter = (request.args.get("filter") or "all").strip().lower()

    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 10))
    except ValueError:
        return error_response(
            "Los parámetros 'page' y 'per_page' deben ser enteros", 400
        )

    if page < 1 or per_page < 1:
        return error_response(
            "Los parámetros 'page' y 'per_page' deben ser mayores a 0", 400
        )
    per_page = min(per_page, 100)

    if feed_filter not in {"all", "top", "unanswered", "ai"}:
        return error_response(
            "Filtro inválido. Valores permitidos: all, top, unanswered, ai", 400
        )

    stmt = db.select(Question)

    if category_filter:
        stmt = stmt.where(
            Question.category.has(func.lower(Category.name) == category_filter.lower())
        )

    if tag_filter:
        stmt = stmt.where(
            Question.tags.any(func.lower(Tag.name) == tag_filter.lower())
        )

    if search_query:
        pattern = f"%{search_query}%"
        stmt = stmt.where(
            or_(Question.title.ilike(pattern), Question.body.ilike(pattern))
        )

    if feed_filter == "unanswered":
        stmt = stmt.where(~Question.responses.any())
    elif feed_filter == "ai":
        stmt = stmt.where(
            Question.responses.any(
                Response.author.has(Author.author_type == Author_Type.LLM)
            )
        )

    stmt = stmt.order_by(Question.post_date.desc(), Question.id.desc())
    all_questions = list(db.session.execute(stmt).scalars().all())

    if feed_filter == "top":
        all_questions.sort(
            key=lambda q: (get_post_score(q), q.post_date, q.id), reverse=True
        )

    total = len(all_questions)
    pages = math.ceil(total / per_page) if total > 0 else 0
    start = (page - 1) * per_page
    page_items = all_questions[start : start + per_page]

    return success_response(
        {
            "total": total,
            "page": page,
            "pages": pages,
            "questions": [serialize_question_summary(q) for q in page_items],
        },
        200,
    )


def get_question(question_id: int):
    question = db.session.get(Question, question_id)
    if question is None:
        return error_response("Pregunta no encontrada", 404)

    return success_response(
        {"question": serialize_question_detail(question, get_current_user_id())},
        200,
    )


@login_required
def create_question():
    data = get_json_body()
    if data is None:
        return error_response("Cuerpo JSON inválido o ausente", 400)

    title = (data.get("title") or "").strip()
    body = (data.get("body") or "").strip()

    if not title or not body:
        return error_response("Los campos 'title' y 'body' son obligatorios", 400)
    if len(title) > 63:
        return error_response("El título no puede superar los 63 caracteres", 400)

    category, err = _resolve_category(data)
    if err is not None:
        return err

    tags, tag_err = _resolve_tags(data.get("tags")) if "tags" in data else ([], None)
    if tag_err is not None:
        db.session.rollback()
        return tag_err

    user = get_current_user()
    question = Question(
        title=title,
        body=body,
        post_date=date.today(),
        author=user,
        category=category,
        tags=tags or [],
    )
    db.session.add(question)
    db.session.commit()

    return success_response(
        {
            "message": "Pregunta creada exitosamente",
            "question_id": question.id,
        },
        201,
    )


@login_required
def update_question(question_id: int):
    question = db.session.get(Question, question_id)
    if question is None:
        return error_response("Pregunta no encontrada", 404)

    user = get_current_user()
    if question.author_id != user.id:
        return error_response("No tenés permisos para editar esta pregunta", 403)

    data = get_json_body()
    if data is None:
        return error_response("Cuerpo JSON inválido o ausente", 400)

    if "title" in data:
        title = (data.get("title") or "").strip()
        if not title:
            return error_response("El campo 'title' no puede estar vacío", 400)
        if len(title) > 63:
            return error_response("El título no puede superar los 63 caracteres", 400)
        question.title = title

    if "body" in data:
        body = (data.get("body") or "").strip()
        if not body:
            return error_response("El campo 'body' no puede estar vacío", 400)
        question.body = body

    if "category" in data or "category_id" in data:
        category, err = _resolve_category(data)
        if err is not None:
            return err
        question.category = category

    if "tags" in data:
        tags, tag_err = _resolve_tags(data.get("tags"))
        if tag_err is not None:
            db.session.rollback()
            return tag_err
        question.tags = tags or []

    db.session.commit()
    return success_response({"message": "Pregunta actualizada"}, 200)


@login_required
def delete_question(question_id: int):
    question = db.session.get(Question, question_id)
    if question is None:
        return error_response("Pregunta no encontrada", 404)

    user = get_current_user()
    if question.author_id != user.id:
        return error_response("No tenés permisos para eliminar esta pregunta", 403)

    db.session.delete(question)
    db.session.commit()
    return success_response({"message": "Pregunta eliminada"}, 200)


@login_required
def vote_question(question_id: int):
    question = db.session.get(Question, question_id)
    if question is None:
        return error_response("Pregunta no encontrada", 404)

    data = get_json_body()
    if data is None:
        return error_response("Cuerpo JSON inválido o ausente", 400)

    direction = (data.get("direction") or "").strip().lower()
    if direction not in {"up", "down"}:
        return error_response("El campo 'direction' debe ser 'up' o 'down'", 400)

    user = get_current_user()
    new_score, user_vote = toggle_vote(question, user.id, direction)
    return success_response(
        {
            "new_score": new_score,
            "user_vote": user_vote,
        },
        200,
    )
