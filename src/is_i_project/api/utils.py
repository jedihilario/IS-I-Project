from __future__ import annotations

import os
from collections.abc import Callable
from datetime import date, datetime
from functools import wraps
from typing import Any

from flask import current_app, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from is_i_project.extensions import db
from is_i_project.models import AI_Author, Author, Post, Question, Response, User, Vote

PASSWORD_HASH_METHOD = "pbkdf2:sha256"


def hash_password(password: str) -> str:
    """Genera un hash compatible con el límite String(127) de User.password."""
    return generate_password_hash(password, method=PASSWORD_HASH_METHOD)


def verify_password(password_hash: str, password: str) -> bool:
    return check_password_hash(password_hash, password)


def success_response(payload: dict[str, Any] | None = None, status_code: int = 200):
    body: dict[str, Any] = {"status": "success"}
    if payload:
        body.update(payload)
    return jsonify(body), status_code


def error_response(message: str, status_code: int = 400):
    return jsonify({"status": "error", "message": message}), status_code


def get_json_body() -> dict[str, Any] | None:
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None
    return data


def format_date_iso(value: date | datetime | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%dT%H:%M:%SZ")
    return f"{value.isoformat()}T00:00:00Z"


def get_avatar_url(user_id: int) -> str | None:
    avatars_dir = os.path.join(current_app.root_path, "static", "uploads", "avatars")
    for ext in (".png", ".jpg", ".jpeg", ".webp"):
        filename = f"user_{user_id}{ext}"
        if os.path.exists(os.path.join(avatars_dir, filename)):
            return f"/static/uploads/avatars/{filename}"
    return None


def get_current_user_id() -> int | None:
    user_id = session.get("user_id")
    if isinstance(user_id, int):
        return user_id
    user_data = session.get("user")
    if isinstance(user_data, dict) and isinstance(user_data.get("id"), int):
        return user_data["id"]
    return None


def get_current_user() -> User | None:
    user_id = get_current_user_id()
    if user_id is None:
        return None
    return db.session.get(User, user_id)


def set_session_user(user: User) -> None:
    session["user_id"] = user.id
    session["user"] = {
        "id": user.id,
        "name": user.name,
        "email": user.email,
    }


def clear_session_user() -> None:
    session.clear()


def login_required(fn: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any):
        if get_current_user() is None:
            return error_response("Autenticación requerida", 401)
        return fn(*args, **kwargs)

    return wrapper


def get_post_score(post: Post) -> int:
    return sum(1 if vote.is_positive else -1 for vote in post.votes)


def get_user_vote(post: Post, user_id: int | None) -> int:
    if user_id is None:
        return 0
    for vote in post.votes:
        if vote.user_id == user_id:
            return 1 if vote.is_positive else -1
    return 0


def toggle_vote(post: Post, user_id: int, direction: str) -> tuple[int, int]:
    is_positive = direction == "up"
    existing = next((v for v in post.votes if v.user_id == user_id), None)

    if existing is not None:
        if existing.is_positive == is_positive:
            db.session.delete(existing)
            user_vote = 0
        else:
            existing.is_positive = is_positive
            existing.date = date.today()
            user_vote = 1 if is_positive else -1
    else:
        db.session.add(
            Vote(
                is_positive=is_positive,
                date=date.today(),
                post_id=post.id,
                user_id=user_id,
            )
        )
        user_vote = 1 if is_positive else -1

    db.session.commit()
    db.session.refresh(post)
    return get_post_score(post), user_vote


def calculate_user_reputation(user: User) -> int:
    q_score = sum(get_post_score(q) for q in user.questions)
    r_score = sum(get_post_score(r) for r in user.responses)
    return max(0, q_score + r_score)


def serialize_user_summary(user: User | None) -> dict[str, Any] | None:
    if user is None:
        return None
    return {
        "id": user.id,
        "name": user.name,
        "reputation": calculate_user_reputation(user),
        "avatar_url": get_avatar_url(user.id),
    }


def serialize_user_detail(user: User) -> dict[str, Any]:
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "reputation": calculate_user_reputation(user),
        "registered_at": None,
        "avatar_url": get_avatar_url(user.id),
        "questions_count": len(user.questions),
        "answers_count": len(user.responses),
    }


def serialize_answer_author(author: Author | None) -> dict[str, Any] | None:
    if author is None:
        return None
    if isinstance(author, AI_Author):
        return {
            "id": author.id,
            "name": "AutorIA",
            "type": "AI",
            "modelName": author.modelName,
            "reputation": 0,
        }
    if isinstance(author, User):
        return {
            "id": author.id,
            "name": author.name,
            "type": "User",
            "reputation": calculate_user_reputation(author),
            "avatar_url": get_avatar_url(author.id),
        }
    return None


def serialize_answer(
    response: Response, current_user_id: int | None = None
) -> dict[str, Any]:
    return {
        "id": response.id,
        "body": response.body,
        "score": get_post_score(response),
        "accepted": bool(response.accepted),
        "user_vote": get_user_vote(response, current_user_id),
        "post_date": format_date_iso(response.post_date),
        "author": serialize_answer_author(response.author),
    }


def serialize_question_summary(question: Question) -> dict[str, Any]:
    responses = question.responses
    return {
        "id": question.id,
        "title": question.title,
        "body": question.body,
        "category": question.category.name if question.category is not None else None,
        "tags": sorted(tag.name for tag in question.tags if tag.name is not None),
        "score": get_post_score(question),
        "answers_count": len(responses),
        "has_accepted": any(bool(r.accepted) for r in responses),
        "has_ai_response": any(isinstance(r.author, AI_Author) for r in responses),
        "views": 0,
        "post_date": format_date_iso(question.post_date),
        "author": serialize_user_summary(question.author),
    }


def serialize_question_detail(
    question: Question, current_user_id: int | None = None
) -> dict[str, Any]:
    answers = [serialize_answer(resp, current_user_id) for resp in question.responses]
    answers.sort(key=lambda item: (not item["accepted"], -item["score"], item["id"]))

    return {
        "id": question.id,
        "title": question.title,
        "body": question.body,
        "category": question.category.name if question.category is not None else None,
        "tags": sorted(tag.name for tag in question.tags if tag.name is not None),
        "score": get_post_score(question),
        "views": 0,
        "post_date": format_date_iso(question.post_date),
        "user_vote": get_user_vote(question, current_user_id),
        "author": serialize_user_summary(question.author),
        "answers": answers,
    }
