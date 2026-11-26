from __future__ import annotations

from datetime import date

from is_i_project.extensions import db
from is_i_project.models import AI_Author, Question, Response, Role, User


def test_public_pages_render_from_sqlite(client, app, create_user_in_db):
    user_id = create_user_in_db(name="Ana Dev", email="ana@example.com")

    with app.app_context():
        user = db.session.get(User, user_id)
        q = Question(
            title="Pregunta en SQLite",
            body="Contenido real guardado en base de datos",
            post_date=date.today(),
            author=user,
        )
        db.session.add(q)
        db.session.commit()
        q_id = q.id

    res_root = client.get("/")
    assert res_root.status_code == 200
    assert "Pregunta en SQLite" in res_root.get_data(as_text=True)

    res_home = client.get("/home")
    assert res_home.status_code == 200
    assert "Pregunta en SQLite" in res_home.get_data(as_text=True)

    res_detail = client.get(f"/preguntas/{q_id}")
    assert res_detail.status_code == 200
    html_detail = res_detail.get_data(as_text=True)
    assert "Pregunta en SQLite" in html_detail
    assert "Contenido real guardado en base de datos" in html_detail

    res_cat = client.get("/categorias")
    assert res_cat.status_code == 200

    res_profile = client.get(f"/usuario/{user_id}")
    assert res_profile.status_code == 200
    assert "Ana Dev" in res_profile.get_data(as_text=True)


def test_web_register_login_logout_and_question_answer_flow(client, app):
    # Registro vía formulario web
    reg = client.post(
        "/registro",
        data={
            "name": "LucasDev",
            "email": "lucas@example.com",
            "password": "password123",
            "password_confirm": "password123",
            "role": "usuario",
        },
        follow_redirects=True,
    )
    assert reg.status_code == 200
    assert "LucasDev" in reg.get_data(as_text=True)

    # Crear pregunta desde formulario web
    created = client.post(
        "/preguntas/nueva",
        data={
            "title": "Duda sobre Flask y SQLite",
            "body": "Cómo integrar vistas Jinja2 con SQLAlchemy?",
            "category": "Backend",
            "tags": "flask,sqlite",
        },
        follow_redirects=True,
    )
    assert created.status_code == 200
    detail_html = created.get_data(as_text=True)
    assert "Duda sobre Flask y SQLite" in detail_html
    assert "Backend" in detail_html
    assert "flask" in detail_html

    with app.app_context():
        q = db.session.execute(
            db.select(Question).where(Question.title == "Duda sobre Flask y SQLite")
        ).scalar_one()
        q_id = q.id

    # Editar pregunta
    edit_page = client.get(f"/preguntas/{q_id}/editar")
    assert edit_page.status_code == 200
    assert "Editar pregunta" in edit_page.get_data(as_text=True)

    edited = client.post(
        f"/preguntas/{q_id}/editar",
        data={
            "title": "Duda editada sobre Flask",
            "body": "Cuerpo actualizado",
            "category": "Backend",
            "tags": "flask,orm",
        },
        follow_redirects=True,
    )
    assert edited.status_code == 200
    assert "Duda editada sobre Flask" in edited.get_data(as_text=True)

    # Publicar respuesta desde formulario web
    answered = client.post(
        f"/preguntas/{q_id}/responder",
        data={"body": "Usá un blueprint o register_web con SQLAlchemy."},
        follow_redirects=True,
    )
    assert answered.status_code == 200
    assert "Usá un blueprint o register_web con SQLAlchemy." in answered.get_data(
        as_text=True
    )

    # La sesión web también autentica llamadas AJAX a la API REST (votos y aceptar)
    vote_res = client.post(f"/api/questions/{q_id}/vote", json={"direction": "up"})
    assert vote_res.status_code == 200
    assert vote_res.get_json()["new_score"] == 1

    with app.app_context():
        ans = db.session.execute(
            db.select(Response).where(Response.question_id == q_id)
        ).scalar_one()
        ans_id = ans.id
        user = db.session.execute(
            db.select(User).where(User.email == "lucas@example.com")
        ).scalar_one()
        user_id = user.id

    accept_res = client.post(f"/api/answers/{ans_id}/accept")
    assert accept_res.status_code == 200

    # Perfil muestra pregunta, respuesta y voto real
    profile_res = client.get(f"/usuario/{user_id}")
    assert profile_res.status_code == 200
    profile_html = profile_res.get_data(as_text=True)
    assert "Duda editada sobre Flask" in profile_html
    assert "Usá un blueprint o register_web con SQLAlchemy." in profile_html

    # Filtros en /home
    assert "Duda editada sobre Flask" in client.get("/home?categoria=Backend").get_data(
        as_text=True
    )
    assert "Duda editada sobre Flask" in client.get("/home?tag=orm").get_data(
        as_text=True
    )
    assert "Duda editada sobre Flask" in client.get("/home?q=editada").get_data(
        as_text=True
    )

    # Eliminar respuesta y luego pregunta
    del_ans = client.get(f"/respuestas/{ans_id}/eliminar", follow_redirects=True)
    assert del_ans.status_code == 200
    with app.app_context():
        assert db.session.get(Response, ans_id) is None

    del_q = client.get(f"/preguntas/{q_id}/eliminar", follow_redirects=True)
    assert del_q.status_code == 200
    with app.app_context():
        assert db.session.get(Question, q_id) is None

    # Logout y re-login
    logout_res = client.get("/logout", follow_redirects=True)
    assert logout_res.status_code == 200
    assert "Iniciar sesión" in logout_res.get_data(as_text=True)

    bad_login = client.post(
        "/login",
        data={"email": "lucas@example.com", "password": "wrongpassword"},
    )
    assert bad_login.status_code == 200
    assert "incorrectos" in bad_login.get_data(as_text=True)

    good_login = client.post(
        "/login",
        data={"email": "lucas@example.com", "password": "password123"},
        follow_redirects=True,
    )
    assert good_login.status_code == 200
    assert "Bienvenido de nuevo" in good_login.get_data(as_text=True)


def test_admin_dashboard_and_ai_config_persistence(client, app):
    # Usuario común no puede entrar a /admin
    client.post(
        "/registro",
        data={
            "name": "NormalUser",
            "email": "normal@example.com",
            "password": "password123",
            "password_confirm": "password123",
            "role": "usuario",
        },
    )
    denied = client.get("/admin", follow_redirects=True)
    assert denied.status_code == 200
    assert "No tenés permisos de administrador" in denied.get_data(as_text=True)
    client.get("/logout")

    # Usuario admin puede acceder y guardar config IA en SQLite
    client.post(
        "/registro",
        data={
            "name": "AdminUser",
            "email": "admin@example.com",
            "password": "password123",
            "password_confirm": "password123",
            "role": "admin",
        },
    )
    dash = client.get("/admin")
    assert dash.status_code == 200
    assert "Panel de administración" in dash.get_data(as_text=True)

    saved = client.post(
        "/admin/config-ia",
        data={
            "ai_provider": "gemini",
            "umbral_horas": "12",
            "timeout_segundos": "45",
            "ai_enabled": "1",
        },
        follow_redirects=True,
    )
    assert saved.status_code == 200
    assert "Configuración de IA guardada" in saved.get_data(as_text=True)

    with app.app_context():
        ai_author = db.session.execute(db.select(AI_Author)).scalar_one()
        assert ai_author.modelName == "Gemini"
        assert ai_author.timeout == 45
        admin_role = db.session.execute(
            db.select(Role).where(Role.name == "admin")
        ).scalar_one()
        assert admin_role is not None
