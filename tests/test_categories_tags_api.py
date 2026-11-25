from __future__ import annotations


def test_categories_crud_and_stats(client, create_user_in_db, login_as):
    create_user_in_db(name="User", email="u@example.com")

    # Sin sesión no puede crear categoría
    assert client.post("/api/categories", json={"name": "Backend"}).status_code == 401

    # Usuario autenticado crea categoría
    login_as("u@example.com")
    c1 = client.post("/api/categories", json={"name": "Backend"})
    assert c1.status_code == 201
    cat_id = c1.get_json()["category"]["id"]

    # Duplicado -> 409
    assert client.post("/api/categories", json={"name": "backend"}).status_code == 409

    # Crear 2 preguntas en Backend y responder solo 1
    q1 = client.post(
        "/api/questions",
        json={"title": "Q1", "body": "Body 1", "category": "Backend"},
    ).get_json()["question_id"]
    client.post(
        "/api/questions",
        json={"title": "Q2", "body": "Body 2", "category": "Backend"},
    )
    client.post(f"/api/questions/{q1}/answers", json={"body": "Ans 1"})

    # Verificar conteos reales
    listing = client.get("/api/categories").get_json()
    assert listing["status"] == "success"
    assert len(listing["categories"]) == 1
    cat_item = listing["categories"][0]
    assert cat_item["id"] == cat_id
    assert cat_item["name"] == "Backend"
    assert cat_item["description"] == ""
    assert cat_item["count"] == 2
    assert cat_item["answered_count"] == 1

    # Actualizar y eliminar categoría
    assert (
        client.put(f"/api/categories/{cat_id}", json={"name": "APIs"}).status_code
        == 200
    )
    assert (
        client.get(f"/api/categories/{cat_id}").get_json()["category"]["name"] == "APIs"
    )

    assert client.delete(f"/api/categories/{cat_id}").status_code == 200
    assert client.get(f"/api/categories/{cat_id}").status_code == 404


def test_tags_crud_and_stats(client, create_user_in_db, login_as):
    create_user_in_db(name="User", email="u@example.com")

    # Sin sesión no puede crear tag
    assert client.post("/api/tags", json={"name": "python"}).status_code == 401

    login_as("u@example.com")
    t1 = client.post("/api/tags", json={"name": "Python"})
    assert t1.status_code == 201
    tag_id = t1.get_json()["tag"]["id"]
    assert t1.get_json()["tag"]["name"] == "python"

    # Crear preguntas con tags
    client.post(
        "/api/questions",
        json={"title": "Q1", "body": "B1", "tags": ["python", "flask"]},
    )
    client.post(
        "/api/questions",
        json={"title": "Q2", "body": "B2", "tags": ["python"]},
    )

    listing = client.get("/api/tags").get_json()
    assert listing["status"] == "success"
    assert listing["tags"][0]["name"] == "python"
    assert listing["tags"][0]["count"] == 2
    assert listing["tags"][1]["name"] == "flask"
    assert listing["tags"][1]["count"] == 1

    # PUT y DELETE
    assert client.put(f"/api/tags/{tag_id}", json={"name": "python3"}).status_code == 200
    assert client.get(f"/api/tags/{tag_id}").get_json()["tag"]["name"] == "python3"

    assert client.delete(f"/api/tags/{tag_id}").status_code == 200
    assert client.get(f"/api/tags/{tag_id}").status_code == 404
