from __future__ import annotations

from datetime import date

from is_i_project.extensions import db
from is_i_project.models import AI_Author, Response
from is_i_project.models.types import Author_Type


def test_questions_crud_and_permissions(client, create_user_in_db, login_as):
    create_user_in_db(name="Autor", email="autor@example.com")
    create_user_in_db(name="Otro", email="otro@example.com")

    # Sin sesión no se puede crear
    unauth = client.post(
        "/api/questions",
        json={"title": "Sin auth", "body": "Cuerpo"},
    )
    assert unauth.status_code == 401

    # Crear pregunta como Autor
    login_as("autor@example.com")
    created = client.post(
        "/api/questions",
        json={
            "title": "Error al conectar Flask con SQLAlchemy",
            "body": "No logra instanciar el pool de conexiones...",
            "category": "Backend",
            "tags": ["flask", "sqlalchemy"],
            "request_ai": True,
            "ai_provider": "openai",
        },
    )
    assert created.status_code == 201
    c_data = created.get_json()
    assert c_data["status"] == "success"
    q_id = c_data["question_id"]

    # Detalle de pregunta
    detail = client.get(f"/api/questions/{q_id}")
    assert detail.status_code == 200
    q = detail.get_json()["question"]
    assert q["id"] == q_id
    assert q["title"] == "Error al conectar Flask con SQLAlchemy"
    assert q["category"] == "Backend"
    assert set(q["tags"]) == {"flask", "sqlalchemy"}
    assert q["score"] == 0
    assert q["user_vote"] == 0
    assert q["author"]["name"] == "Autor"
    assert q["answers"] == []

    # Otro usuario no puede editar ni eliminar
    login_as("otro@example.com")
    forbid_edit = client.put(
        f"/api/questions/{q_id}",
        json={"title": "Intento", "body": "Intento"},
    )
    assert forbid_edit.status_code == 403
    forbid_del = client.delete(f"/api/questions/{q_id}")
    assert forbid_del.status_code == 403

    # Autor puede editar
    login_as("autor@example.com")
    updated = client.put(
        f"/api/questions/{q_id}",
        json={
            "title": "Nuevo título corregido",
            "body": "Nuevo cuerpo detallado...",
            "category": "Backend",
            "tags": ["flask", "orm"],
        },
    )
    assert updated.status_code == 200
    after_edit = client.get(f"/api/questions/{q_id}").get_json()["question"]
    assert after_edit["title"] == "Nuevo título corregido"
    assert set(after_edit["tags"]) == {"flask", "orm"}

    # Autor puede eliminar
    deleted = client.delete(f"/api/questions/{q_id}")
    assert deleted.status_code == 200
    assert client.get(f"/api/questions/{q_id}").status_code == 404


def test_questions_filters_pagination_votes_and_ai_response(
    app, client, create_user_in_db, login_as
):
    create_user_in_db(name="Alice", email="alice@example.com")
    create_user_in_db(name="Bob", email="bob@example.com")

    login_as("alice@example.com")
    q1 = client.post(
        "/api/questions",
        json={
            "title": "Pregunta Python Strategy",
            "body": "Cómo aplicar Strategy en Python",
            "category": "Backend",
            "tags": ["python", "patterns"],
        },
    ).get_json()["question_id"]

    q2 = client.post(
        "/api/questions",
        json={
            "title": "Pregunta CSS Grid",
            "body": "Layout responsive",
            "category": "Frontend",
            "tags": ["css"],
        },
    ).get_json()["question_id"]

    # Agregar respuesta de IA a q1
    with app.app_context():
        ai_author = AI_Author(
            author_type=Author_Type.LLM,
            modelName="GPT-4o",
            timeout=30,
        )
        db.session.add(ai_author)
        db.session.flush()
        ai_resp = Response(
            body="Respuesta generada automáticamente",
            post_date=date.today(),
            accepted=False,
            author_id=ai_author.id,
            question_id=q1,
        )
        db.session.add(ai_resp)
        db.session.commit()

    # Votar q2 positivamente con 2 usuarios para que quede primera en filter=top
    v1 = client.post(f"/api/questions/{q2}/vote", json={"direction": "up"})
    assert v1.status_code == 200
    assert v1.get_json() == {"status": "success", "new_score": 1, "user_vote": 1}

    # Toggle off (mismo voto retira el voto)
    v_off = client.post(f"/api/questions/{q2}/vote", json={"direction": "up"})
    assert v_off.get_json() == {"status": "success", "new_score": 0, "user_vote": 0}

    # Volver a votar up y luego invertir a down
    client.post(f"/api/questions/{q2}/vote", json={"direction": "up"})
    v_down = client.post(f"/api/questions/{q2}/vote", json={"direction": "down"})
    assert v_down.get_json() == {"status": "success", "new_score": -1, "user_vote": -1}

    # Votar q1 positivamente
    client.post(f"/api/questions/{q1}/vote", json={"direction": "up"})
    login_as("bob@example.com")
    client.post(f"/api/questions/{q1}/vote", json={"direction": "up"})

    # Filtro top -> q1 tiene score 2, q2 tiene -1
    top = client.get("/api/questions?filter=top").get_json()
    assert top["total"] == 2
    assert [item["id"] for item in top["questions"]] == [q1, q2]
    assert top["questions"][0]["score"] == 2

    # Filtro unanswered -> solo q2
    unanswered = client.get("/api/questions?filter=unanswered").get_json()
    assert unanswered["total"] == 1
    assert unanswered["questions"][0]["id"] == q2

    # Filtro ai -> solo q1
    ai_only = client.get("/api/questions?filter=ai").get_json()
    assert ai_only["total"] == 1
    assert ai_only["questions"][0]["id"] == q1
    assert ai_only["questions"][0]["has_ai_response"] is True

    # Filtro category, tag y búsqueda q
    by_cat = client.get("/api/questions?category=Frontend").get_json()
    assert by_cat["total"] == 1 and by_cat["questions"][0]["id"] == q2

    by_tag = client.get("/api/questions?tag=patterns").get_json()
    assert by_tag["total"] == 1 and by_tag["questions"][0]["id"] == q1

    by_q = client.get("/api/questions?q=responsive").get_json()
    assert by_q["total"] == 1 and by_q["questions"][0]["id"] == q2

    # Paginación
    page1 = client.get("/api/questions?page=1&per_page=1").get_json()
    assert page1["total"] == 2
    assert page1["pages"] == 2
    assert len(page1["questions"]) == 1

    # Detalle de q1 incluye respuesta de AI_Author con formato del contrato
    q1_detail = client.get(f"/api/questions/{q1}").get_json()["question"]
    assert q1_detail["user_vote"] == 1
    assert len(q1_detail["answers"]) == 1
    ai_ans = q1_detail["answers"][0]
    assert ai_ans["author"]["type"] == "AI"
    assert ai_ans["author"]["name"] == "AutorIA"
    assert ai_ans["author"]["modelName"] == "GPT-4o"
