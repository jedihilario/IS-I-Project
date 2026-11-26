from __future__ import annotations

import os
from datetime import date

from flask import (
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from sqlalchemy import func, or_

from is_i_project.api.controllers.questions_controller import (
    _resolve_category,
    _resolve_tags,
)
from is_i_project.api.utils import (
    clear_session_user,
    get_current_user,
    get_current_user_id,
    get_post_score,
    get_user_vote,
    hash_password,
    set_session_user,
    verify_password,
)
from is_i_project.extensions import db
from is_i_project.models import (
    AI_Author,
    Author,
    Category,
    Question,
    Response,
    Role,
    Tag,
    User,
)
from is_i_project.models.types import Author_Type
from is_i_project.web.presenters import (
    ALLOWED_AVATAR_EXTENSIONS,
    PROVIDER_TO_MODEL,
    SimplePagination,
    build_answer_vm,
    build_category_vm,
    build_global_stats,
    build_question_vm,
    build_tag_vm,
    build_user_vm,
    build_vote_vm,
    get_ai_config,
    get_avatars_folder,
    is_admin_user,
)


def _get_or_create_role(role_name: str) -> Role:
    normalized = role_name.strip().lower()
    if normalized not in {"admin", "usuario"}:
        normalized = "usuario"
    role = db.session.execute(
        db.select(Role).where(func.lower(Role.name) == normalized)
    ).scalar_one_or_none()
    if role is None:
        role = Role(name=normalized)
        db.session.add(role)
        db.session.flush()
    return role


def index():
    return home()


def home():
    category_filter = (
        request.args.get("category") or request.args.get("categoria") or ""
    ).strip()
    tag_filter = (request.args.get("tag") or "").strip()
    search_query = (request.args.get("q") or "").strip()
    feed_filter = (request.args.get("filter") or "all").strip().lower()

    try:
        page = max(1, int(request.args.get("page", 1)))
    except ValueError:
        page = 1
    per_page = 10

    stmt = db.select(Question)

    if category_filter:
        normalized_cat = category_filter.replace("-", " ").lower()
        stmt = stmt.where(
            Question.category.has(
                or_(
                    func.lower(Category.name) == category_filter.lower(),
                    func.lower(Category.name) == normalized_cat,
                )
            )
        )

    if tag_filter:
        stmt = stmt.where(
            Question.tags.any(func.lower(Tag.name) == tag_filter.lower())
        )

    if search_query:
        pattern = f"%{search_query}%"
        stmt = stmt.where(
            or_(Question.title.ilike(pattern), Question.body.ilike(pattern))
        )

    if feed_filter == "unanswered":
        stmt = stmt.where(~Question.responses.any())
    elif feed_filter == "ai":
        stmt = stmt.where(
            Question.responses.any(
                Response.author.has(Author.author_type == Author_Type.LLM)
            )
        )

    stmt = stmt.order_by(Question.post_date.desc(), Question.id.desc())
    all_questions = list(db.session.execute(stmt).scalars().all())

    if feed_filter == "top":
        all_questions.sort(
            key=lambda q: (get_post_score(q), q.post_date, q.id), reverse=True
        )

    pagination = SimplePagination(page=page, per_page=per_page, total=len(all_questions))
    start = (page - 1) * per_page
    page_questions = [
        build_question_vm(q) for q in all_questions[start : start + per_page]
    ]

    categories_rows = db.session.execute(db.select(Category)).scalars().all()
    popular_categories = sorted(
        (build_category_vm(c) for c in categories_rows),
        key=lambda c: (-c.count, c.name.lower()),
    )[:5]

    users_rows = db.session.execute(db.select(User)).scalars().all()
    top_users = sorted(
        (u_vm for u in users_rows if (u_vm := build_user_vm(u)) is not None),
        key=lambda u: (-u.reputation, u.name.lower()),
    )[:5]

    tags_rows = db.session.execute(db.select(Tag)).scalars().all()
    popular_tags = sorted(
        (build_tag_vm(t) for t in tags_rows),
        key=lambda t: (-t.count, t.name.lower()),
    )[:10]

    return render_template(
        "home.html",
        questions=page_questions,
        pagination=pagination,
        stats=build_global_stats(),
        popular_categories=popular_categories,
        top_users=top_users,
        popular_tags=popular_tags,
        active_filter=feed_filter,
    )


def question_detail(question_id: int):
    question = db.session.get(Question, question_id)
    if question is None:
        abort(404)

    current_user_id = get_current_user_id()
    question_vm = build_question_vm(question)

    answers = [build_answer_vm(r, current_user_id) for r in question.responses]
    answers.sort(key=lambda a: (not a.accepted, -a.score, a.id))

    similar_stmt = db.select(Question).where(Question.id != question.id)
    if question.category_id is not None:
        similar_stmt = similar_stmt.where(Question.category_id == question.category_id)
    similar_rows = list(
        db.session.execute(
            similar_stmt.order_by(Question.post_date.desc(), Question.id.desc()).limit(3)
        )
        .scalars()
        .all()
    )
    if len(similar_rows) < 3:
        existing_ids = {question.id, *(q.id for q in similar_rows)}
        extra_rows = (
            db.session.execute(
                db.select(Question)
                .where(Question.id.notin_(existing_ids))
                .order_by(Question.post_date.desc(), Question.id.desc())
                .limit(3 - len(similar_rows))
            )
            .scalars()
            .all()
        )
        similar_rows.extend(extra_rows)

    return render_template(
        "question_detail.html",
        question=question_vm,
        answers=answers,
        user_vote=get_user_vote(question, current_user_id),
        similar_questions=[build_question_vm(q) for q in similar_rows],
    )


def question_new():
    user = get_current_user()
    if user is None:
        flash("Debés iniciar sesión para publicar una pregunta.", "info")
        return redirect(url_for("login"))

    categories_rows = (
        db.session.execute(db.select(Category).order_by(Category.name.asc()))
        .scalars()
        .all()
    )
    categories_vms = [build_category_vm(c) for c in categories_rows]

    if request.method == "POST":
        title = (request.form.get("title") or request.form.get("titulo") or "").strip()
        body = (request.form.get("body") or request.form.get("cuerpo") or "").strip()
        raw_category = (
            request.form.get("category") or request.form.get("categoria") or ""
        ).strip()
        raw_tags = (request.form.get("tags") or "").strip()

        if not title or not body:
            flash("El título y el cuerpo de la pregunta son obligatorios.", "error")
            return render_template("question_new.html", categories=categories_vms)
        if len(title) > 63:
            flash("El título no puede superar los 63 caracteres.", "error")
            return render_template("question_new.html", categories=categories_vms)

        category, cat_err = _resolve_category({"category": raw_category})
        if cat_err is not None:
            db.session.rollback()
            flash("La categoría indicada no es válida.", "error")
            return render_template("question_new.html", categories=categories_vms)

        tags, tag_err = _resolve_tags(raw_tags) if raw_tags else ([], None)
        if tag_err is not None:
            db.session.rollback()
            flash("Alguno de los tags ingresados no es válido.", "error")
            return render_template("question_new.html", categories=categories_vms)

        question = Question(
            title=title,
            body=body,
            post_date=date.today(),
            author=user,
            category=category,
            tags=tags or [],
        )
        db.session.add(question)
        db.session.commit()

        flash("Pregunta publicada exitosamente.", "success")
        return redirect(url_for("question_detail", question_id=question.id))

    return render_template("question_new.html", categories=categories_vms)


def question_edit(question_id: int):
    user = get_current_user()
    if user is None:
        flash("Debés iniciar sesión para editar una pregunta.", "info")
        return redirect(url_for("login"))

    question = db.session.get(Question, question_id)
    if question is None:
        abort(404)

    if question.author_id != user.id and not is_admin_user(user):
        flash("No tenés permisos para editar esta pregunta.", "error")
        return redirect(url_for("question_detail", question_id=question.id))

    categories_rows = (
        db.session.execute(db.select(Category).order_by(Category.name.asc()))
        .scalars()
        .all()
    )
    categories_vms = [build_category_vm(c) for c in categories_rows]
    edit_question = build_question_vm(question)

    if request.method == "POST":
        title = (request.form.get("title") or request.form.get("titulo") or "").strip()
        body = (request.form.get("body") or request.form.get("cuerpo") or "").strip()
        raw_category = (
            request.form.get("category") or request.form.get("categoria") or ""
        ).strip()
        raw_tags = (request.form.get("tags") or "").strip()

        if not title or not body:
            flash("El título y el cuerpo de la pregunta son obligatorios.", "error")
            return render_template(
                "question_new.html",
                categories=categories_vms,
                edit_question=edit_question,
            )
        if len(title) > 63:
            flash("El título no puede superar los 63 caracteres.", "error")
            return render_template(
                "question_new.html",
                categories=categories_vms,
                edit_question=edit_question,
            )

        category, cat_err = _resolve_category({"category": raw_category})
        if cat_err is not None:
            db.session.rollback()
            flash("La categoría indicada no es válida.", "error")
            return render_template(
                "question_new.html",
                categories=categories_vms,
                edit_question=edit_question,
            )

        tags, tag_err = _resolve_tags(raw_tags) if raw_tags else ([], None)
        if tag_err is not None:
            db.session.rollback()
            flash("Alguno de los tags ingresados no es válido.", "error")
            return render_template(
                "question_new.html",
                categories=categories_vms,
                edit_question=edit_question,
            )

        question.title = title
        question.body = body
        question.category = category
        question.tags = tags or []
        db.session.commit()

        flash("Pregunta actualizada correctamente.", "success")
        return redirect(url_for("question_detail", question_id=question.id))

    return render_template(
        "question_new.html",
        categories=categories_vms,
        edit_question=edit_question,
    )


def question_delete(question_id: int):
    user = get_current_user()
    if user is None:
        flash("Debés iniciar sesión para eliminar una pregunta.", "info")
        return redirect(url_for("login"))

    question = db.session.get(Question, question_id)
    if question is None:
        abort(404)

    if question.author_id != user.id and not is_admin_user(user):
        flash("No tenés permisos para eliminar esta pregunta.", "error")
        return redirect(url_for("question_detail", question_id=question.id))

    db.session.delete(question)
    db.session.commit()
    flash("Pregunta eliminada.", "info")
    return redirect(url_for("home"))


def answer_create(question_id: int):
    user = get_current_user()
    if user is None:
        flash("Debés iniciar sesión para responder.", "info")
        return redirect(url_for("login"))

    question = db.session.get(Question, question_id)
    if question is None:
        abort(404)

    body = (request.form.get("body") or request.form.get("cuerpo") or "").strip()
    if not body:
        flash("La respuesta no puede estar vacía.", "error")
        return redirect(url_for("question_detail", question_id=question.id))

    answer = Response(
        body=body,
        post_date=date.today(),
        accepted=False,
        author=user,
        question=question,
    )
    db.session.add(answer)
    db.session.commit()

    flash("Respuesta publicada exitosamente.", "success")
    return redirect(url_for("question_detail", question_id=question.id))


def answer_delete(answer_id: int):
    user = get_current_user()
    if user is None:
        flash("Debés iniciar sesión para eliminar una respuesta.", "info")
        return redirect(url_for("login"))

    answer = db.session.get(Response, answer_id)
    if answer is None:
        abort(404)

    if answer.author_id != user.id and not is_admin_user(user):
        flash("No tenés permisos para eliminar esta respuesta.", "error")
        return redirect(url_for("question_detail", question_id=answer.question_id))

    question_id = answer.question_id
    db.session.delete(answer)
    db.session.commit()
    flash("Respuesta eliminada.", "info")
    return redirect(url_for("question_detail", question_id=question_id))


def login():
    if get_current_user() is not None:
        return redirect(url_for("home"))

    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""

        if not email or not password:
            flash("Por favor completá todos los campos.", "error")
            return render_template("auth/auth.html", active_tab="login")

        user = db.session.execute(
            db.select(User).where(User.email == email)
        ).scalar_one_or_none()
        if user is None or not verify_password(user.password, password):
            flash("Email o contraseña incorrectos.", "error")
            return render_template("auth/auth.html", active_tab="login")

        set_session_user(user)
        session.permanent = bool(request.form.get("remember_me"))
        flash(f"¡Bienvenido de nuevo, {user.name}!", "success")
        return redirect(url_for("home"))

    return render_template("auth/auth.html", active_tab="login")


def register():
    if get_current_user() is not None:
        return redirect(url_for("home"))

    if request.method == "POST":
        name = (request.form.get("name") or request.form.get("nombre") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        password_confirm = request.form.get("password_confirm")
        role_name = (
            request.form.get("role") or request.form.get("rol") or "usuario"
        ).strip()

        if not name or not email or not password:
            flash("Por favor completá todos los campos obligatorios.", "error")
            return render_template("auth/auth.html", active_tab="register")
        if len(name) > 31:
            flash("El nombre no puede superar los 31 caracteres.", "error")
            return render_template("auth/auth.html", active_tab="register")
        if len(email) > 127 or "@" not in email:
            flash("El email ingresado no es válido.", "error")
            return render_template("auth/auth.html", active_tab="register")
        if len(password) < 8:
            flash("La contraseña debe tener al menos 8 caracteres.", "error")
            return render_template("auth/auth.html", active_tab="register")
        if password_confirm is not None and password != password_confirm:
            flash("Las contraseñas no coinciden.", "error")
            return render_template("auth/auth.html", active_tab="register")

        existing = db.session.execute(
            db.select(User).where(User.email == email)
        ).scalar_one_or_none()
        if existing is not None:
            flash("Ya existe un usuario registrado con ese email.", "error")
            return render_template("auth/auth.html", active_tab="register")

        role = _get_or_create_role(role_name)
        user = User(
            name=name,
            email=email,
            password=hash_password(password),
            role_id=role.id,
        )
        db.session.add(user)
        db.session.commit()

        set_session_user(user)
        flash(f"Cuenta creada exitosamente. ¡Bienvenido, {user.name}!", "success")
        return redirect(url_for("home"))

    return render_template("auth/auth.html", active_tab="register")


def logout():
    clear_session_user()
    flash("Sesión cerrada correctamente.", "info")
    return redirect(url_for("login"))


def profile(user_id: int):
    user = db.session.get(User, user_id)
    if user is None:
        abort(404)

    current_user_id = get_current_user_id()
    user_vm = build_user_vm(user)

    questions = sorted(
        (build_question_vm(q) for q in user.questions),
        key=lambda q: (q.post_date or date.min, q.id),
        reverse=True,
    )
    answers = sorted(
        (
            build_answer_vm(r, current_user_id, include_question=True)
            for r in user.responses
        ),
        key=lambda a: (a.post_date or date.min, a.id),
        reverse=True,
    )
    votes = [v_vm for v in user.votes if (v_vm := build_vote_vm(v)) is not None]
    votes.sort(key=lambda v: (v.date or date.min, v.id), reverse=True)

    return render_template(
        "user/profile.html",
        user=user_vm,
        questions=questions,
        answers=answers,
        votes=votes,
    )


def profile_photo_upload():
    user = get_current_user()
    if user is None:
        flash("Debés iniciar sesión para cambiar tu foto de perfil.", "error")
        return redirect(url_for("login"))

    file = request.files.get("avatar")
    if file is None or not file.filename:
        flash("No se seleccionó ninguna imagen válida.", "error")
        return redirect(url_for("profile", user_id=user.id))

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_AVATAR_EXTENSIONS:
        flash("Formato no soportado. Usá PNG, JPG, JPEG o WEBP.", "error")
        return redirect(url_for("profile", user_id=user.id))

    avatars_folder = get_avatars_folder()
    avatars_folder.mkdir(parents=True, exist_ok=True)

    for old_ext in ALLOWED_AVATAR_EXTENSIONS:
        old_path = avatars_folder / f"user_{user.id}{old_ext}"
        if old_path.exists():
            old_path.unlink()

    file.save(avatars_folder / f"user_{user.id}{ext}")
    flash("¡Foto de perfil actualizada exitosamente!", "success")
    return redirect(url_for("profile", user_id=user.id))


def categories():
    categories_rows = (
        db.session.execute(db.select(Category).order_by(Category.name.asc()))
        .scalars()
        .all()
    )
    tags_rows = (
        db.session.execute(db.select(Tag).order_by(Tag.name.asc())).scalars().all()
    )

    category_vms = sorted(
        (build_category_vm(c) for c in categories_rows),
        key=lambda c: (-c.count, c.name.lower()),
    )
    tag_vms = sorted(
        (build_tag_vm(t) for t in tags_rows),
        key=lambda t: (-t.count, t.name.lower()),
    )

    return render_template(
        "categories.html",
        categories=category_vms,
        tags=tag_vms,
        stats=build_global_stats(),
    )


def admin_dashboard():
    user = get_current_user()
    if user is None:
        flash("Debés iniciar sesión para acceder al panel de administración.", "info")
        return redirect(url_for("login"))
    if not is_admin_user(user):
        flash("No tenés permisos de administrador.", "error")
        return redirect(url_for("home"))

    users_rows = (
        db.session.execute(db.select(User).order_by(User.id.asc())).scalars().all()
    )
    recent_q_rows = (
        db.session.execute(
            db.select(Question)
            .order_by(Question.post_date.desc(), Question.id.desc())
            .limit(50)
        )
        .scalars()
        .all()
    )

    return render_template(
        "admin/dashboard.html",
        stats=build_global_stats(),
        users=[u_vm for u in users_rows if (u_vm := build_user_vm(u)) is not None],
        recent_questions=[build_question_vm(q) for q in recent_q_rows],
        ai_config=get_ai_config(),
    )


def admin_config_ai():
    user = get_current_user()
    if user is None:
        flash("Debés iniciar sesión para acceder al panel de administración.", "info")
        return redirect(url_for("login"))
    if not is_admin_user(user):
        flash("No tenés permisos de administrador.", "error")
        return redirect(url_for("home"))

    provider = (request.form.get("ai_provider") or "openai").strip().lower()
    if provider not in PROVIDER_TO_MODEL:
        provider = "openai"

    try:
        hours_threshold = max(1, min(720, int(request.form.get("umbral_horas", 24))))
    except ValueError:
        hours_threshold = 24

    try:
        timeout = max(5, min(300, int(request.form.get("timeout_segundos", 60))))
    except ValueError:
        timeout = 60

    enabled = bool(request.form.get("ai_enabled"))

    ai_author = (
        db.session.execute(db.select(AI_Author).order_by(AI_Author.id.asc()))
        .scalars()
        .first()
    )
    if ai_author is None:
        ai_author = AI_Author(
            modelName=PROVIDER_TO_MODEL[provider],
            timeout=timeout,
        )
        db.session.add(ai_author)
    else:
        ai_author.modelName = PROVIDER_TO_MODEL[provider]
        ai_author.timeout = timeout
    db.session.commit()

    current_app.config["AI_CONFIG"] = {
        "provider": provider,
        "hours_threshold": hours_threshold,
        "timeout": timeout,
        "enabled": enabled,
    }

    flash("Configuración de IA guardada correctamente.", "success")
    return redirect(url_for("admin_dashboard"))
