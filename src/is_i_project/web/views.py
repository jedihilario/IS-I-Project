from __future__ import annotations

from datetime import date

from flask import abort, flash, redirect, render_template, request, url_for

from is_i_project.api.controllers.admin_controller import update_ai_config_record
from is_i_project.api.controllers.answers_controller import (
    create_answer_record,
    delete_answer_record,
)
from is_i_project.api.controllers.auth_controller import (
    authenticate_user_record,
    logout_user_session,
    register_user_record,
)
from is_i_project.api.controllers.categories_controller import get_all_categories
from is_i_project.api.controllers.questions_controller import (
    create_question_record,
    delete_question_record,
    get_question_record,
    get_similar_questions,
    query_questions,
    update_question_record,
)
from is_i_project.api.controllers.tags_controller import get_all_tags
from is_i_project.api.controllers.users_controller import (
    get_all_users,
    get_user_record,
)
from is_i_project.api.utils import (
    ControllerError,
    get_current_user,
    get_current_user_id,
    get_user_vote,
    is_admin_user,
)
from is_i_project.web.presenters import (
    SimplePagination,
    build_answer_vm,
    build_category_vm,
    build_global_stats,
    build_question_vm,
    build_tag_vm,
    build_user_vm,
    build_vote_vm,
    get_ai_config,
)


def index():
    return home()


def home():
    category_filter = (
        request.args.get("category") or request.args.get("categoria") or ""
    ).strip()
    tag_filter = (request.args.get("tag") or "").strip()
    search_query = (request.args.get("q") or "").strip()
    feed_filter = (request.args.get("filter") or "all").strip().lower()
    if feed_filter not in {"all", "top", "unanswered", "ai"}:
        feed_filter = "all"

    try:
        page = max(1, int(request.args.get("page", 1)))
    except ValueError:
        page = 1
    per_page = 10

    page_rows, total, _ = query_questions(
        category_filter=category_filter,
        tag_filter=tag_filter,
        search_query=search_query,
        feed_filter=feed_filter,
        page=page,
        per_page=per_page,
    )

    pagination = SimplePagination(page=page, per_page=per_page, total=total)
    page_questions = [build_question_vm(q) for q in page_rows]

    popular_categories = sorted(
        (build_category_vm(c) for c in get_all_categories()),
        key=lambda c: (-c.count, c.name.lower()),
    )[:5]
    top_users = sorted(
        (u_vm for u in get_all_users() if (u_vm := build_user_vm(u)) is not None),
        key=lambda u: (-u.reputation, u.name.lower()),
    )[:5]
    popular_tags = sorted(
        (build_tag_vm(t) for t in get_all_tags()),
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
    try:
        question = get_question_record(question_id)
    except ControllerError:
        abort(404)

    current_user_id = get_current_user_id()
    answers = [build_answer_vm(r, current_user_id) for r in question.responses]
    answers.sort(key=lambda a: (not a.accepted, -a.score, a.id))

    similar_rows = get_similar_questions(question, limit=3)

    return render_template(
        "question_detail.html",
        question=build_question_vm(question),
        answers=answers,
        user_vote=get_user_vote(question, current_user_id),
        similar_questions=[build_question_vm(q) for q in similar_rows],
    )


def question_new():
    user = get_current_user()
    if user is None:
        flash("Debés iniciar sesión para publicar una pregunta.", "info")
        return redirect(url_for("login"))

    categories_vms = [build_category_vm(c) for c in get_all_categories()]

    if request.method == "POST":
        title = request.form.get("title") or request.form.get("titulo") or ""
        body = request.form.get("body") or request.form.get("cuerpo") or ""
        raw_category = (
            request.form.get("category") or request.form.get("categoria") or ""
        )
        raw_tags = request.form.get("tags") or ""

        try:
            question = create_question_record(
                user,
                title=title,
                body=body,
                category=raw_category,
                tags=raw_tags,
            )
        except ControllerError as exc:
            flash(exc.message, "error")
            return render_template("question_new.html", categories=categories_vms)

        flash("Pregunta publicada exitosamente.", "success")
        return redirect(url_for("question_detail", question_id=question.id))

    return render_template("question_new.html", categories=categories_vms)


def question_edit(question_id: int):
    user = get_current_user()
    if user is None:
        flash("Debés iniciar sesión para editar una pregunta.", "info")
        return redirect(url_for("login"))

    try:
        question = get_question_record(question_id)
    except ControllerError:
        abort(404)

    if question.author_id != user.id and not is_admin_user(user):
        flash("No tenés permisos para editar esta pregunta.", "error")
        return redirect(url_for("question_detail", question_id=question.id))

    categories_vms = [build_category_vm(c) for c in get_all_categories()]
    edit_question = build_question_vm(question)

    if request.method == "POST":
        title = request.form.get("title") or request.form.get("titulo") or ""
        body = request.form.get("body") or request.form.get("cuerpo") or ""
        raw_category = (
            request.form.get("category") or request.form.get("categoria") or ""
        )
        raw_tags = request.form.get("tags") or ""

        try:
            update_question_record(
                question_id,
                user,
                title=title,
                body=body,
                category=raw_category,
                tags=raw_tags,
                allow_admin=True,
            )
        except ControllerError as exc:
            flash(exc.message, "error")
            return render_template(
                "question_new.html",
                categories=categories_vms,
                edit_question=edit_question,
            )

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

    try:
        delete_question_record(question_id, user, allow_admin=True)
    except ControllerError as exc:
        if exc.status_code == 404:
            abort(404)
        flash(exc.message, "error")
        return redirect(url_for("question_detail", question_id=question_id))

    flash("Pregunta eliminada.", "info")
    return redirect(url_for("home"))


def answer_create(question_id: int):
    user = get_current_user()
    if user is None:
        flash("Debés iniciar sesión para responder.", "info")
        return redirect(url_for("login"))

    body = request.form.get("body") or request.form.get("cuerpo") or ""
    try:
        create_answer_record(question_id, user, body=body)
    except ControllerError as exc:
        if exc.status_code == 404:
            abort(404)
        flash(exc.message, "error")
        return redirect(url_for("question_detail", question_id=question_id))

    flash("Respuesta publicada exitosamente.", "success")
    return redirect(url_for("question_detail", question_id=question_id))


def answer_delete(answer_id: int):
    user = get_current_user()
    if user is None:
        flash("Debés iniciar sesión para eliminar una respuesta.", "info")
        return redirect(url_for("login"))

    try:
        question_id = delete_answer_record(answer_id, user, allow_admin=True)
    except ControllerError as exc:
        if exc.status_code == 404:
            abort(404)
        flash(exc.message, "error")
        return redirect(url_for("home"))

    flash("Respuesta eliminada.", "info")
    return redirect(url_for("question_detail", question_id=question_id))


def login():
    if get_current_user() is not None:
        return redirect(url_for("home"))

    if request.method == "POST":
        email = request.form.get("email") or ""
        password = request.form.get("password") or ""
        remember_me = bool(request.form.get("remember_me"))

        try:
            user = authenticate_user_record(
                email=email, password=password, remember_me=remember_me
            )
        except ControllerError as exc:
            flash(exc.message, "error")
            return render_template("auth/auth.html", active_tab="login")

        flash(f"¡Bienvenido de nuevo, {user.name}!", "success")
        return redirect(url_for("home"))

    return render_template("auth/auth.html", active_tab="login")


def register():
    if get_current_user() is not None:
        return redirect(url_for("home"))

    if request.method == "POST":
        name = request.form.get("name") or request.form.get("nombre") or ""
        email = request.form.get("email") or ""
        password = request.form.get("password") or ""
        password_confirm = request.form.get("password_confirm")
        role_name = request.form.get("role") or request.form.get("rol") or "usuario"

        try:
            user = register_user_record(
                name=name,
                email=email,
                password=password,
                role_name=role_name,
                password_confirm=password_confirm,
                min_password_length=8,
            )
        except ControllerError as exc:
            flash(exc.message, "error")
            return render_template("auth/auth.html", active_tab="register")

        flash(f"Cuenta creada exitosamente. ¡Bienvenido, {user.name}!", "success")
        return redirect(url_for("home"))

    return render_template("auth/auth.html", active_tab="register")


def logout():
    logout_user_session()
    flash("Sesión cerrada correctamente.", "info")
    return redirect(url_for("login"))


def profile(user_id: int):
    try:
        user = get_user_record(user_id)
    except ControllerError:
        abort(404)

    current_user_id = get_current_user_id()
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
        user=build_user_vm(user),
        questions=questions,
        answers=answers,
        votes=votes,
    )


def categories():
    category_vms = sorted(
        (build_category_vm(c) for c in get_all_categories()),
        key=lambda c: (-c.count, c.name.lower()),
    )
    tag_vms = sorted(
        (build_tag_vm(t) for t in get_all_tags()),
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

    recent_rows, _, _ = query_questions(page=1, per_page=50)

    return render_template(
        "admin/dashboard.html",
        stats=build_global_stats(),
        users=[u_vm for u in get_all_users() if (u_vm := build_user_vm(u)) is not None],
        recent_questions=[build_question_vm(q) for q in recent_rows],
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

    try:
        hours_threshold = int(request.form.get("umbral_horas", 24))
    except ValueError:
        hours_threshold = 24

    try:
        timeout = int(request.form.get("timeout_segundos", 60))
    except ValueError:
        timeout = 60

    update_ai_config_record(
        provider=request.form.get("ai_provider") or "openai",
        hours_threshold=hours_threshold,
        timeout=timeout,
        enabled=bool(request.form.get("ai_enabled")),
    )

    flash("Configuración de IA guardada correctamente.", "success")
    return redirect(url_for("admin_dashboard"))
