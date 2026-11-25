from __future__ import annotations

from sqlalchemy import func

from is_i_project.api.utils import (
    error_response,
    get_json_body,
    login_required,
    success_response,
)
from is_i_project.extensions import db
from is_i_project.models import Category


def _serialize_category(category: Category) -> dict:
    questions = category.questions
    return {
        "id": category.id,
        "name": category.name,
        "description": "",
        "count": len(questions),
        "answered_count": sum(1 for q in questions if q.responses),
    }


def list_categories():
    categories = db.session.execute(
        db.select(Category).order_by(Category.name.asc())
    ).scalars().all()
    return success_response(
        {"categories": [_serialize_category(cat) for cat in categories]}, 200
    )


def get_category(category_id: int):
    category = db.session.get(Category, category_id)
    if category is None:
        return error_response("Categoría no encontrada", 404)
    return success_response({"category": _serialize_category(category)}, 200)


@login_required
def create_category():
    data = get_json_body()
    if data is None:
        return error_response("Cuerpo JSON inválido o ausente", 400)

    name = (data.get("name") or "").strip()
    if not name:
        return error_response("El campo 'name' es obligatorio", 400)
    if len(name) > 63:
        return error_response(
            "El nombre de la categoría no puede superar los 63 caracteres", 400
        )

    existing = db.session.execute(
        db.select(Category).where(func.lower(Category.name) == name.lower())
    ).scalar_one_or_none()
    if existing is not None:
        return error_response("Ya existe una categoría con ese nombre", 409)

    category = Category(name=name)
    db.session.add(category)
    db.session.commit()

    return success_response(
        {
            "message": "Categoría creada exitosamente",
            "category": _serialize_category(category),
        },
        201,
    )


@login_required
def update_category(category_id: int):
    category = db.session.get(Category, category_id)
    if category is None:
        return error_response("Categoría no encontrada", 404)

    data = get_json_body()
    if data is None:
        return error_response("Cuerpo JSON inválido o ausente", 400)

    name = (data.get("name") or "").strip()
    if not name:
        return error_response("El campo 'name' es obligatorio", 400)
    if len(name) > 63:
        return error_response(
            "El nombre de la categoría no puede superar los 63 caracteres", 400
        )

    duplicate = db.session.execute(
        db.select(Category).where(
            func.lower(Category.name) == name.lower(),
            Category.id != category.id,
        )
    ).scalar_one_or_none()
    if duplicate is not None:
        return error_response("Ya existe otra categoría con ese nombre", 409)

    category.name = name
    db.session.commit()

    return success_response({"message": "Categoría actualizada"}, 200)


@login_required
def delete_category(category_id: int):
    category = db.session.get(Category, category_id)
    if category is None:
        return error_response("Categoría no encontrada", 404)

    db.session.delete(category)
    db.session.commit()

    return success_response({"message": "Categoría eliminada"}, 200)
