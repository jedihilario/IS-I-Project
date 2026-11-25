from __future__ import annotations


def test_answers_crud_vote_and_accept(client, create_user_in_db, login_as):
    create_user_in_db(name="Autor Pregunta", email="qauthor@example.com")
    create_user_in_db(name="Respondedor", email="responder@example.com")

    # Crear pregunta
    login_as("qauthor@example.com")
    q_id = client.post(
        "/api/questions",
        json={"title": "Duda SQLAlchemy", "body": "Cómo hacer joins"},
    ).get_json()["question_id"]

    # Publicar dos respuestas como Respondedor
    login_as("responder@example.com")
    r1 = client.post(
        f"/api/questions/{q_id}/answers",
        json={"body": "Primera respuesta"},
    )
    assert r1.status_code == 201
    a1_id = r1.get_json()["answer_id"]

    r2 = client.post(
        f"/api/questions/{q_id}/answers",
        json={"body": "Segunda respuesta"},
    )
    assert r2.status_code == 201
    a2_id = r2.get_json()["answer_id"]

    # Editar respuesta propia
    upd = client.put(f"/api/answers/{a1_id}", json={"body": "Primera respuesta editada"})
    assert upd.status_code == 200

    # Votar respuesta
    vote = client.post(f"/api/answers/{a1_id}/vote", json={"direction": "up"})
    assert vote.status_code == 200
    assert vote.get_json() == {"status": "success", "new_score": 1, "user_vote": 1}

    # Respondedor NO puede aceptar respuesta (solo autor de la pregunta)
    forbid_accept = client.post(f"/api/answers/{a1_id}/accept")
    assert forbid_accept.status_code == 403

    # Autor de la pregunta acepta a1, luego cambia a a2
    login_as("qauthor@example.com")
    acc1 = client.post(f"/api/answers/{a1_id}/accept")
    assert acc1.status_code == 200
    assert acc1.get_json() == {"status": "success", "accepted_answer_id": a1_id}

    acc2 = client.post(f"/api/answers/{a2_id}/accept")
    assert acc2.status_code == 200
    assert acc2.get_json() == {"status": "success", "accepted_answer_id": a2_id}

    # Verificar que solo a2 está aceptada y figura primera
    detail = client.get(f"/api/questions/{q_id}").get_json()["question"]
    assert detail["answers"][0]["id"] == a2_id
    assert detail["answers"][0]["accepted"] is True
    assert detail["answers"][1]["id"] == a1_id
    assert detail["answers"][1]["accepted"] is False

    # Autor de la pregunta no puede borrar respuesta ajena
    assert client.delete(f"/api/answers/{a1_id}").status_code == 403

    # Autor de la respuesta sí puede eliminarla
    login_as("responder@example.com")
    del_resp = client.delete(f"/api/answers/{a1_id}")
    assert del_resp.status_code == 200
    detail_after = client.get(f"/api/questions/{q_id}").get_json()["question"]
    assert len(detail_after["answers"]) == 1
    assert detail_after["answers"][0]["id"] == a2_id
