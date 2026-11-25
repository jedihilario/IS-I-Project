from __future__ import annotations


def test_users_list_detail_and_create(client, create_user_in_db, login_as):
    u1_id = create_user_in_db(name="User 1", email="u1@example.com")
    create_user_in_db(name="User 2", email="u2@example.com")

    # User 1 crea pregunta y User 2 responde y vota
    login_as("u1@example.com")
    q_id = client.post(
        "/api/questions",
        json={"title": "Mi pregunta", "body": "Detalle"},
    ).get_json()["question_id"]

    login_as("u2@example.com")
    client.post(f"/api/questions/{q_id}/vote", json={"direction": "up"})
    client.post(f"/api/questions/{q_id}/answers", json={"body": "Mi respuesta"})

    # Perfil de User 1 (GET /api/users/<id>)
    profile = client.get(f"/api/users/{u1_id}")
    assert profile.status_code == 200
    user_data = profile.get_json()["user"]
    assert user_data["id"] == u1_id
    assert user_data["name"] == "User 1"
    assert user_data["email"] == "u1@example.com"
    assert user_data["reputation"] == 1
    assert user_data["questions_count"] == 1
    assert user_data["answers_count"] == 0

    # Listado público
    users_list = client.get("/api/users").get_json()
    assert users_list["status"] == "success"
    assert len(users_list["users"]) == 2

    # PUT y DELETE en /api/users/<id> no están habilitados -> 405 Method Not Allowed
    assert client.put(f"/api/users/{u1_id}", json={"name": "Edit"}).status_code == 405
    assert client.delete(f"/api/users/{u1_id}").status_code == 405

    # Usuario autenticado crea otro usuario vía POST /api/users
    created = client.post(
        "/api/users",
        json={
            "name": "Usuario Nuevo",
            "email": "nuevo@example.com",
            "password": "secret",
        },
    )
    assert created.status_code == 201
    new_id = created.get_json()["user"]["id"]
    assert client.get(f"/api/users/{new_id}").status_code == 200


def test_admin_delete_user_without_roles(client, create_user_in_db, login_as):
    u1_id = create_user_in_db(name="User 1", email="u1@example.com")
    create_user_in_db(name="User 2", email="u2@example.com")

    # User 1 crea una pregunta para verificar cascada al eliminar desde admin
    login_as("u1@example.com")
    q_id = client.post(
        "/api/questions",
        json={"title": "Pregunta u1", "body": "Cuerpo"},
    ).get_json()["question_id"]
    client.post("/api/auth/logout")

    # Sin sesión devuelve 401
    assert client.delete(f"/api/admin/users/{u1_id}").status_code == 401

    # Endpoint de cambio de rol eliminado -> 404
    login_as("u2@example.com")
    assert (
        client.patch(f"/api/admin/users/{u1_id}/role", json={"role": "admin"}).status_code
        == 404
    )

    # Eliminación vía /api/admin/users/<id> funciona con sesión activa y limpia cascada
    deleted = client.delete(f"/api/admin/users/{u1_id}")
    assert deleted.status_code == 200
    assert deleted.get_json() == {
        "status": "success",
        "message": "Usuario eliminado",
    }
    assert client.get(f"/api/users/{u1_id}").status_code == 404
    assert client.get(f"/api/questions/{q_id}").status_code == 404
