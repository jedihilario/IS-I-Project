from __future__ import annotations

from sqlalchemy import func

from is_i_project.api.utils import (
    error_response,
    get_json_body,
    login_required,
    success_response,
)
from is_i_project.extensions import db
from is_i_project.models import Tag


def _serialize_tag(tag: Tag) -> dict:
    return {
        "id": tag.id,
        "name": tag.name,
        "count": len(tag.questions),
    }


def list_tags():
    tags = db.session.execute(db.select(Tag).order_by(Tag.name.asc())).scalars().all()
    serialized = [_serialize_tag(tag) for tag in tags]
    serialized.sort(key=lambda item: (-item["count"], item["name"] or ""))
    return success_response({"tags": serialized}, 200)


def get_tag(tag_id: int):
    tag = db.session.get(Tag, tag_id)
    if tag is None:
        return error_response("Tag no encontrado", 404)
    return success_response({"tag": _serialize_tag(tag)}, 200)


@login_required
def create_tag():
    data = get_json_body()
    if data is None:
        return error_response("Cuerpo JSON inválido o ausente", 400)

    name = (data.get("name") or "").strip().lower()
    if not name:
        return error_response("El campo 'name' es obligatorio", 400)
    if len(name) > 63:
        return error_response(
            "El nombre del tag no puede superar los 63 caracteres", 400
        )

    existing = db.session.execute(
        db.select(Tag).where(func.lower(Tag.name) == name)
    ).scalar_one_or_none()
    if existing is not None:
        return error_response("Ya existe un tag con ese nombre", 409)

    tag = Tag(name=name)
    db.session.add(tag)
    db.session.commit()

    return success_response(
        {
            "message": "Tag creado exitosamente",
            "tag": _serialize_tag(tag),
        },
        201,
    )


@login_required
def update_tag(tag_id: int):
    tag = db.session.get(Tag, tag_id)
    if tag is None:
        return error_response("Tag no encontrado", 404)

    data = get_json_body()
    if data is None:
        return error_response("Cuerpo JSON inválido o ausente", 400)

    name = (data.get("name") or "").strip().lower()
    if not name:
        return error_response("El campo 'name' es obligatorio", 400)
    if len(name) > 63:
        return error_response(
            "El nombre del tag no puede superar los 63 caracteres", 400
        )

    duplicate = db.session.execute(
        db.select(Tag).where(func.lower(Tag.name) == name, Tag.id != tag.id)
    ).scalar_one_or_none()
    if duplicate is not None:
        return error_response("Ya existe otro tag con ese nombre", 409)

    tag.name = name
    db.session.commit()

    return success_response({"message": "Tag actualizado"}, 200)


@login_required
def delete_tag(tag_id: int):
    tag = db.session.get(Tag, tag_id)
    if tag is None:
        return error_response("Tag no encontrado", 404)

    db.session.delete(tag)
    db.session.commit()

    return success_response({"message": "Tag eliminado"}, 200)
