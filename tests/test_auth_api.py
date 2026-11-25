from __future__ import annotations


def test_register_login_me_logout_flow(client):
    # Registro
    res = client.post(
        "/api/auth/register",
        json={
            "name": "Valentín Tello",
            "email": "valentin@example.com",
            "password": "password123",
        },
    )
    assert res.status_code == 201
    data = res.get_json()
    assert data["status"] == "success"
    assert data["user"]["name"] == "Valentín Tello"
    assert data["user"]["email"] == "valentin@example.com"
    assert "password" not in data["user"]

    # Email duplicado
    dup = client.post(
        "/api/auth/register",
        json={
            "name": "Otro",
            "email": "valentin@example.com",
            "password": "password123",
        },
    )
    assert dup.status_code == 409
    assert dup.get_json()["status"] == "error"

    # /me autenticado
    me = client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.get_json()["user"]["email"] == "valentin@example.com"

    # Logout
    logout = client.post("/api/auth/logout")
    assert logout.status_code == 200

    # /me sin sesión
    me_after = client.get("/api/auth/me")
    assert me_after.status_code == 401

    # Login incorrecto
    bad_login = client.post(
        "/api/auth/login",
        json={"email": "valentin@example.com", "password": "wrong"},
    )
    assert bad_login.status_code == 401

    # Login correcto
    ok_login = client.post(
        "/api/auth/login",
        json={"email": "valentin@example.com", "password": "password123"},
    )
    assert ok_login.status_code == 200
    assert ok_login.get_json()["user"]["email"] == "valentin@example.com"


def test_register_validation_errors(client):
    res = client.post("/api/auth/register", json={"name": "", "email": "invalid"})
    assert res.status_code == 400
    assert res.get_json()["status"] == "error"


def test_api_unknown_route_returns_json_404(client):
    res = client.get("/api/ruta-inexistente")
    assert res.status_code == 404
    assert res.is_json
    assert res.get_json()["status"] == "error"
