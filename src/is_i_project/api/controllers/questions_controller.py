from __future__ import annotations

import math
from datetime import date
from typing import Any

from flask import request
from sqlalchemy import func, or_

from is_i_project.api.utils import (
    ControllerError,
    error_response,
    get_current_user,
    get_current_user_id,
    get_json_body,
    get_post_score,
    is_admin_user,
    login_required,
    serialize_question_detail,
    serialize_question_summary,
    success_response,
    toggle_vote,
)
from is_i_project.extensions import db
from is_i_project.models import Author, Category, Question, Response, Tag, User
from is_i_project.models.types import Author_Type

_UNSET: Any = object()


def _resolve_category(
    *, category: Any = None, category_id: Any = None
) -> Category | None:
    if category_id is not None:
        if not isinstance(category_id, int):
            raise ControllerError("'category_id' debe ser un entero", 400)
        cat = db.session.get(Category, category_id)
        if cat is None:
            raise ControllerError("Categoría no encontrada", 404)
        return cat

    if category is not None:
        cat_name = str(category).strip()
        if not cat_name:
            return None
        if len(cat_name) > 63:
            raise ControllerError(
                "El nombre de la categoría no puede superar los 63 caracteres", 400
            )
        cat = db.session.execute(
            db.select(Category).where(func.lower(Category.name) == cat_name.lower())
        ).scalar_one_or_none()
        if cat is None:
            cat = Category(name=cat_name)
            db.session.add(cat)
            db.session.flush()
        return cat

    return None


def _resolve_tags(raw_tags: Any) -> list[Tag]:
    if raw_tags is None:
        return []
    if isinstance(raw_tags, str):
        tag_names = [t.strip().lower() for t in raw_tags.split(",") if t.strip()]
    elif isinstance(raw_tags, list):
        tag_names = [str(t).strip().lower() for t in raw_tags if str(t).strip()]
    else:
        raise ControllerError("'tags' debe ser una lista de strings", 400)

    tags: list[Tag] = []
    for name in dict.fromkeys(tag_names):
        if len(name) > 63:
            raise ControllerError(f"El tag '{name}' supera los 63 caracteres", 400)
        tag = db.session.execute(
            db.select(Tag).where(func.lower(Tag.name) == name)
        ).scalar_one_or_none()
        if tag is None:
            tag = Tag(name=name)
            db.session.add(tag)
            db.session.flush()
        tags.append(tag)

    return tags


def query_questions(
    *,
    category_filter: str = "",
    tag_filter: str = "",
    search_query: str = "",
    feed_filter: str = "all",
    page: int = 1,
    per_page: int = 10,
) -> tuple[list[Question], int, int]:
    if page < 1 or per_page < 1:
        raise ControllerError(
            "Los parámetros 'page' y 'per_page' deben ser mayores a 0", 400
        )
    per_page = min(per_page, 100)

    if feed_filter not in {"all", "top", "unanswered", "ai"}:
        raise ControllerError(
            "Filtro inválido. Valores permitidos: all, top, unanswered, ai", 400
        )

    stmt = db.select(Question)

    if category_filter:
        normalized_cat = category_filter.replace("-", " ").lower()
        stmt = stmt.where(
            Question.category.has(
                or_(
                    func.lower(Category.name) == category_filter.lower(),
                    func.lower(Category.name) == normalized_cat,
                )
            )
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
    return all_questions[start : start + per_page], total, pages


def get_question_record(question_id: int) -> Question:
    question = db.session.get(Question, question_id)
    if question is None:
        raise ControllerError("Pregunta no encontrada", 404)
    return question


def get_similar_questions(question: Question, limit: int = 3) -> list[Question]:
    similar_stmt = db.select(Question).where(Question.id != question.id)
    if question.category_id is not None:
        similar_stmt = similar_stmt.where(Question.category_id == question.category_id)
    similar_rows = list(
        db.session.execute(
            similar_stmt.order_by(Question.post_date.desc(), Question.id.desc()).limit(
                limit
            )
        )
        .scalars()
        .all()
    )
    if len(similar_rows) < limit:
        existing_ids = {question.id, *(q.id for q in similar_rows)}
        extra_rows = (
            db.session.execute(
                db.select(Question)
                .where(Question.id.notin_(existing_ids))
                .order_by(Question.post_date.desc(), Question.id.desc())
                .limit(limit - len(similar_rows))
            )
            .scalars()
            .all()
        )
        similar_rows.extend(extra_rows)
    return similar_rows


def create_question_record(
    user: User,
    *,
    title: str,
    body: str,
    category: Any = None,
    category_id: Any = None,
    tags: Any = None,
) -> Question:
    clean_title = (title or "").strip()
    clean_body = (body or "").strip()

    if not clean_title or not clean_body:
        raise ControllerError("Los campos 'title' y 'body' son obligatorios", 400)
    if len(clean_title) > 63:
        raise ControllerError("El título no puede superar los 63 caracteres", 400)

    try:
        resolved_category = _resolve_category(
            category=category, category_id=category_id
        )
        resolved_tags = _resolve_tags(tags)
    except ControllerError:
        db.session.rollback()
        raise

    question = Question(
        title=clean_title,
        body=clean_body,
        post_date=date.today(),
        author=user,
        category=resolved_category,
        tags=resolved_tags,
    )
    db.session.add(question)
    db.session.commit()
    return question


def update_question_record(
    question_id: int,
    user: User,
    *,
    title: Any = _UNSET,
    body: Any = _UNSET,
    category: Any = _UNSET,
    category_id: Any = _UNSET,
    tags: Any = _UNSET,
    allow_admin: bool = False,
) -> Question:
    question = get_question_record(question_id)

    if question.author_id != user.id and not (allow_admin and is_admin_user(user)):
        raise ControllerError("No tenés permisos para editar esta pregunta", 403)

    if title is not _UNSET:
        clean_title = (title or "").strip()
        if not clean_title:
            raise ControllerError("El campo 'title' no puede estar vacío", 400)
        if len(clean_title) > 63:
            raise ControllerError("El título no puede superar los 63 caracteres", 400)
        question.title = clean_title

    if body is not _UNSET:
        clean_body = (body or "").strip()
        if not clean_body:
            raise ControllerError("El campo 'body' no puede estar vacío", 400)
        question.body = clean_body

    try:
        if category is not _UNSET or category_id is not _UNSET:
            question.category = _resolve_category(
                category=None if category is _UNSET else category,
                category_id=None if category_id is _UNSET else category_id,
            )

        if tags is not _UNSET:
            question.tags = _resolve_tags(tags)
    except ControllerError:
        db.session.rollback()
        raise

    db.session.commit()
    return question


def delete_question_record(
    question_id: int, user: User, *, allow_admin: bool = False
) -> None:
    question = get_question_record(question_id)

    if question.author_id != user.id and not (allow_admin and is_admin_user(user)):
        raise ControllerError("No tenés permisos para eliminar esta pregunta", 403)

    db.session.delete(question)
    db.session.commit()


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

    try:
        page_items, total, pages = query_questions(
            category_filter=category_filter,
            tag_filter=tag_filter,
            search_query=search_query,
            feed_filter=feed_filter,
            page=page,
            per_page=per_page,
        )
    except ControllerError as exc:
        return error_response(exc.message, exc.status_code)

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
    try:
        question = get_question_record(question_id)
    except ControllerError as exc:
        return error_response(exc.message, exc.status_code)

    return success_response(
        {"question": serialize_question_detail(question, get_current_user_id())},
        200,
    )


@login_required
def create_question():
    data = get_json_body()
    if data is None:
        return error_response("Cuerpo JSON inválido o ausente", 400)

    user = get_current_user()
    try:
        question = create_question_record(
            user,
            title=data.get("title") or "",
            body=data.get("body") or "",
            category=data.get("category"),
            category_id=data.get("category_id"),
            tags=data.get("tags") if "tags" in data else None,
        )
    except ControllerError as exc:
        return error_response(exc.message, exc.status_code)

    return success_response(
        {
            "message": "Pregunta creada exitosamente",
            "question_id": question.id,
        },
        201,
    )


@login_required
def update_question(question_id: int):
    data = get_json_body()
    if data is None:
        return error_response("Cuerpo JSON inválido o ausente", 400)

    user = get_current_user()
    try:
        update_question_record(
            question_id,
            user,
            title=data.get("title") if "title" in data else _UNSET,
            body=data.get("body") if "body" in data else _UNSET,
            category=data.get("category") if "category" in data else _UNSET,
            category_id=data.get("category_id") if "category_id" in data else _UNSET,
            tags=data.get("tags") if "tags" in data else _UNSET,
        )
    except ControllerError as exc:
        return error_response(exc.message, exc.status_code)

    return success_response({"message": "Pregunta actualizada"}, 200)


@login_required
def delete_question(question_id: int):
    user = get_current_user()
    try:
        delete_question_record(question_id, user)
    except ControllerError as exc:
        return error_response(exc.message, exc.status_code)

    return success_response({"message": "Pregunta eliminada"}, 200)


@login_required
def vote_question(question_id: int):
    try:
        question = get_question_record(question_id)
    except ControllerError as exc:
        return error_response(exc.message, exc.status_code)

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
