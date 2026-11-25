from __future__ import annotations

import pytest

from is_i_project import create_app
from is_i_project.api.utils import hash_password
from is_i_project.extensions import db
from is_i_project.models import User


@pytest.fixture()
def app():
    app = create_app("testing")
    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        TESTING=True,
        SECRET_KEY="test-secret-key",
    )
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def create_user_in_db(app):
    def _create(
        name: str = "Usuario Test",
        email: str = "user@example.com",
        password: str = "secret123",
    ) -> int:
        with app.app_context():
            user = User(
                name=name,
                email=email,
                password=hash_password(password),
            )
            db.session.add(user)
            db.session.commit()
            return user.id

    return _create


@pytest.fixture()
def login_as(client):
    def _login(email: str, password: str = "secret123"):
        resp = client.post(
            "/api/auth/login",
            json={"email": email, "password": password},
        )
        assert resp.status_code == 200
        return resp.get_json()

    return _login
