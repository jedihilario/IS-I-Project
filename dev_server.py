"""
Servidor de desarrollo para previsualizar el frontend.
Usa datos de prueba (mock) — NO conecta a ninguna base de datos.

Ejecutar:
    uv run python dev_server.py
    o
    python dev_server.py
Luego abrir: http://localhost:5000
"""

import os
import random
from datetime import datetime, timedelta
from flask import Flask, render_template, redirect, url_for, request, session, flash

app = Flask(
    __name__,
    template_folder="src/is_i_project/templates",
    static_folder="src/is_i_project/static",
)
app.secret_key = "dev-secret-key-only"

AVATARS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src", "is_i_project", "static", "uploads", "avatars")
os.makedirs(AVATARS_FOLDER, exist_ok=True)


def get_user_avatar(user_id):
    for ext in [".png", ".jpg", ".jpeg", ".webp"]:
        filename = f"user_{user_id}{ext}"
        if os.path.exists(os.path.join(AVATARS_FOLDER, filename)):
            return f"/static/uploads/avatars/{filename}"
    return None


# ─── Mock data helpers ──────────────────────────────────────

def mock_user(id=1, nombre="Valentín Tello", rol="admin"):
    class U:
        pass
    u = U()
    u.id = id
    u.name = nombre
    u.nombre = nombre
    u.email = f"{nombre.lower().replace(' ', '.')}@example.com"
    u.role = rol
    u.rol = rol
    u.type = "User"
    u.tipo = "Usuario"
    u.reputation = random.randint(50, 3500)
    u.reputacion = u.reputation
    u.created_at = datetime(2024, 3, 15)
    u.registered_at = u.created_at
    u.fecha_registro = u.created_at
    u.questions_count = random.randint(2, 25)
    u.preguntas_count = u.questions_count
    u.answers_count = random.randint(5, 60)
    u.respuestas_count = u.answers_count
    u.avatar_url = get_user_avatar(u.id)
    u.foto = u.avatar_url
    u.getNombreVisible = lambda: u.name
    u.get_display_name = lambda: u.name
    return u


def get_current_user():
    user_data = session.get("user")
    if not user_data:
        return None
    class U:
        pass
    u = U()
    u.id = user_data.get("id", 1)
    u.name = user_data.get("name") or user_data.get("nombre", "Usuario")
    u.nombre = u.name
    u.email = user_data.get("email", "usuario@example.com")
    u.role = user_data.get("role") or user_data.get("rol", "usuario")
    u.rol = u.role
    u.type = "User"
    u.tipo = "Usuario"
    u.reputation = user_data.get("reputation") or user_data.get("reputacion", 100)
    u.reputacion = u.reputation
    u.created_at = datetime(2024, 3, 15)
    u.registered_at = u.created_at
    u.fecha_registro = u.created_at
    u.questions_count = user_data.get("questions_count") or user_data.get("preguntas_count", 0)
    u.preguntas_count = u.questions_count
    u.answers_count = user_data.get("answers_count") or user_data.get("respuestas_count", 0)
    u.respuestas_count = u.answers_count
    u.avatar_url = get_user_avatar(u.id)
    u.foto = u.avatar_url
    u.getNombreVisible = lambda: u.name
    u.get_display_name = lambda: u.name
    return u


def mock_tag(nombre):
    class T:
        pass
    t = T()
    t.name = nombre
    t.nombre = nombre
    t.count = random.randint(3, 50)
    return t


def mock_categoria(nombre, count=None, desc=None):
    class C:
        pass
    c = C()
    c.name = nombre
    c.nombre = nombre
    c.count = count or random.randint(5, 80)
    c.description = desc or f"Preguntas relacionadas con {nombre}"
    c.descripcion = c.description
    c.answered_count = c.count // 2
    c.respondidas = c.answered_count
    return c


def mock_pregunta(id, titulo, cuerpo="", tags=None, categoria="Backend",
                  votos=None, respuestas_count=None, tiene_aceptada=False,
                  tiene_respuesta_ia=False, dias_atras=1):
    class Q:
        pass
    class A:
        pass
    q = Q()
    q.id = id
    q.title = titulo
    q.titulo = titulo
    q.body = cuerpo or f"<p>{titulo}</p><p>Este es el cuerpo de ejemplo de la pregunta. Podría incluir código, diagramas o cualquier detalle relevante para obtener una buena respuesta.</p>"
    q.cuerpo = q.body
    q.tags = tags or ["python", "flask"]
    q.category = categoria
    q.categoria = categoria
    q.score = votos if votos is not None else random.randint(-2, 42)
    q.votes = q.score
    q.votos = q.score
    q.puntuacion = q.score
    q.answers_count = respuestas_count if respuestas_count is not None else random.randint(0, 8)
    q.respuestas_count = q.answers_count
    q.has_accepted = tiene_aceptada
    q.tiene_aceptada = tiene_aceptada
    q.has_ai_response = tiene_respuesta_ia
    q.tiene_respuesta_ia = tiene_respuesta_ia
    q.views = random.randint(10, 500)
    q.vistas = q.views
    q.post_date = datetime.now() - timedelta(days=dias_atras)
    q.fecha_publicacion = q.post_date
    q.author = mock_user(id=id + 10, nombre=random.choice(["Román M.", "Juan A.", "Tomás M.", "Hilario Y.", "Valentín T."]))
    q.autor = q.author
    return q


def mock_respuesta(id, cuerpo, es_aceptada=False, es_ia=False, votos=None):
    class R:
        pass
    class A:
        pass
    r = R()
    r.id = id
    r.body = f"<p>{cuerpo}</p><p>Espero que esto ayude. Si tenés alguna duda adicional, no dudes en preguntar.</p>"
    r.cuerpo = r.body
    r.accepted = es_aceptada
    r.es_aceptada = es_aceptada
    r.score = votos if votos is not None else random.randint(0, 20)
    r.puntuacion = r.score
    r.user_vote = 0
    r.post_date = datetime.now() - timedelta(hours=random.randint(1, 48))
    r.fecha_publicacion = r.post_date
    if es_ia:
        a = A()
        a.type = "AI"
        a.tipo = "IA"
        a.id = 999
        a.modelName = "GPT-4o"
        a.nombreModelo = "GPT-4o"
        a.reputation = 0
        a.reputacion = 0
        a.getNombreVisible = lambda: "AutorIA"
        a.get_display_name = lambda: "AutorIA"
        r.author = a
        r.autor = a
    else:
        r.author = mock_user(id=id + 20, nombre=random.choice(["Román M.", "Hilario Y.", "Juan A."]))
        r.autor = r.author
    r.question = mock_pregunta(id + 100, "Pregunta de ejemplo")
    r.pregunta = r.question
    return r


SAMPLE_QUESTIONS = [
    mock_pregunta(1, "¿Cómo implementar el patrón Strategy en Python con SQLAlchemy?",
                  tags=["python", "sqlalchemy", "patrones"], categoria="Backend",
                  votos=15, respuestas_count=3, tiene_aceptada=True, tiene_respuesta_ia=False, dias_atras=2),
    mock_pregunta(2, "Error al configurar Flask con blueprints y Jinja2",
                  tags=["flask", "jinja2", "blueprints"], categoria="Backend",
                  votos=8, respuestas_count=1, tiene_aceptada=False, tiene_respuesta_ia=True, dias_atras=1),
    mock_pregunta(3, "¿Cuál es la diferencia entre Factory Method y Abstract Factory?",
                  tags=["patrones", "poo", "diseño"], categoria="Algoritmos",
                  votos=22, respuestas_count=5, tiene_aceptada=True, tiene_respuesta_ia=True, dias_atras=5),
    mock_pregunta(4, "¿Cómo manejar migraciones con Alembic en un proyecto Flask?",
                  tags=["flask", "alembic", "migraciones", "sql"], categoria="Base de datos",
                  votos=11, respuestas_count=2, tiene_aceptada=False, tiene_respuesta_ia=False, dias_atras=3),
    mock_pregunta(5, "Autenticación JWT en Flask sin librerías externas",
                  tags=["flask", "jwt", "seguridad", "api"], categoria="Seguridad",
                  votos=0, respuestas_count=0, tiene_aceptada=False, tiene_respuesta_ia=False, dias_atras=0),
    mock_pregunta(6, "Optimizar consultas N+1 con SQLAlchemy y lazy loading",
                  tags=["sqlalchemy", "performance", "sql"], categoria="Base de datos",
                  votos=18, respuestas_count=4, tiene_aceptada=True, tiene_respuesta_ia=False, dias_atras=7),
]

CURRENT_USER = mock_user()

STATS = {
    "total_preguntas": 142,
    "total_respuestas": 387,
    "total_usuarios": 48,
    "respuestas_ia": 23,
    "nuevos_usuarios_semana": 7,
    "nuevas_preguntas_semana": 12,
    "nuevas_respuestas_semana": 31,
    "pct_ia": 6,
}

CATEGORIAS = [
    mock_categoria("Backend", 42, "Flask, Django, APIs REST y más"),
    mock_categoria("Frontend", 28, "HTML, CSS, JavaScript y frameworks"),
    mock_categoria("Base de datos", 35, "SQL, NoSQL, ORM y migraciones"),
    mock_categoria("Algoritmos", 20, "Estructuras de datos y complejidad"),
    mock_categoria("DevOps", 10, "Docker, CI/CD y despliegue"),
    mock_categoria("IA / ML", 15, "Machine learning y modelos de lenguaje"),
    mock_categoria("Seguridad", 12, "Autenticación, criptografía y vulnerabilidades"),
    mock_categoria("General", 8, "Preguntas generales de programación"),
]

TAGS = [mock_tag(t) for t in [
    "python", "flask", "javascript", "sql", "api-rest", "sqlalchemy",
    "html", "css", "git", "docker", "testing", "orm", "async",
    "autenticacion", "jinja2", "postgresql", "react", "typescript",
    "algoritmos", "seguridad", "patrones", "poo",
]]

TOP_USUARIOS = [
    mock_user(2, "Hilario Y.", "admin"),
    mock_user(3, "Román M.", "moderador"),
    mock_user(4, "Tomás M.", "usuario"),
    mock_user(5, "Juan A.", "usuario"),
]

# ─── Template globals & Auth guard ──────────────────────────

@app.context_processor
def inject_globals():
    def csrf_token():
        return "mock-csrf-token"
    return dict(
        current_user=get_current_user(),
        csrf_token=csrf_token,
        unanswered_count=sum(1 for q in SAMPLE_QUESTIONS if q.respuestas_count == 0),
    )


@app.before_request
def require_login():
    # Recursos estáticos siempre permitidos
    if request.path.startswith("/static") or request.path == "/favicon.ico":
        return None

    public_endpoints = {"index", "login", "register", "static"}
    endpoint = request.endpoint

    user = get_current_user()

    # Si NO está logueado o registrado, no puede acceder a nada fuera de la autenticación
    if not user and endpoint not in public_endpoints:
        flash("Debés iniciar sesión o registrarte para acceder a la plataforma.", "info")
        return redirect(url_for("index"))

    # Si YA está logueado y va a login/registro, llevar directo a /home
    if user and endpoint in {"index", "login", "register"}:
        return redirect(url_for("home"))


# ─── Routes ─────────────────────────────────────────────────

@app.route("/", endpoint="index")
def index():
    tab = request.args.get("tab", "login")
    return render_template("auth/auth.html", active_tab=tab)


@app.route("/home", endpoint="home")
def home():
    return render_template("home.html",
        questions=SAMPLE_QUESTIONS,
        stats=STATS,
        categorias_populares=CATEGORIAS[:5],
        top_usuarios=TOP_USUARIOS,
        tags_populares=TAGS[:10],
    )


@app.route("/preguntas/<int:question_id>")
def question_detail(question_id):
    pregunta = next((q for q in SAMPLE_QUESTIONS if q.id == question_id), SAMPLE_QUESTIONS[0])
    if pregunta.respuestas_count == 0 and not pregunta.tiene_respuesta_ia:
        respuestas = []
    elif pregunta.tiene_respuesta_ia and pregunta.respuestas_count == 0:
        respuestas = [
            mock_respuesta(
                999,
                f"Respuesta generada automáticamente por IA para tu consulta sobre: <strong>{pregunta.titulo}</strong>.",
                es_ia=True,
                votos=1
            )
        ]
        pregunta.respuestas_count = 1
    else:
        respuestas = [
            mock_respuesta(1, "Podés implementar el patrón Strategy definiendo una clase abstracta `IEstrategia` con el método `ejecutar()`, y luego clases concretas que lo implementen.", es_aceptada=True, votos=12),
            mock_respuesta(2, "Aquí hay un ejemplo completo con Python:\n\n```python\nclass AutorIA:\n    def __init__(self, estrategia):\n        self.estrategia = estrategia\n    \n    def generar(self, prompt):\n        return self.estrategia.generarContenido(prompt)\n```", es_ia=True, votos=8),
            mock_respuesta(3, "También podés usar `Protocol` de Python 3.8+ en lugar de ABCMeta para definir la interfaz, es más pythónico.", votos=5),
        ]
    return render_template("question_detail.html",
        pregunta=pregunta,
        respuestas=respuestas,
        user_vote=0,
        preguntas_similares=SAMPLE_QUESTIONS[:3],
    )


@app.route("/preguntas/nueva", methods=["GET", "POST"], endpoint="question_new")
@app.route("/preguntas/crear", methods=["POST"], endpoint="question_create")
def question_new():
    if request.method == "POST":
        titulo = (request.form.get("title") or request.form.get("titulo", "")).strip()
        cuerpo = (request.form.get("body") or request.form.get("cuerpo", "")).strip()
        categoria = (request.form.get("category") or request.form.get("categoria", "")).strip() or "General"
        raw_tags = request.form.get("tags", "").strip()
        tags = [t.strip() for t in raw_tags.split(",") if t.strip()] if raw_tags else ["general"]
        solicitar_ia = bool(request.form.get("request_ai") or request.form.get("solicitar_ia"))

        nueva_id = max((q.id for q in SAMPLE_QUESTIONS), default=0) + 1
        nueva_q = mock_pregunta(
            id=nueva_id,
            titulo=titulo or "Pregunta sin título",
            cuerpo=f"<p>{cuerpo}</p>" if cuerpo else "",
            tags=tags,
            categoria=categoria,
            votos=0,
            respuestas_count=0,
            tiene_aceptada=False,
            tiene_respuesta_ia=solicitar_ia,
            dias_atras=0,
        )
        nueva_q.autor = get_current_user() or mock_user()
        nueva_q.author = nueva_q.autor
        SAMPLE_QUESTIONS.insert(0, nueva_q)
        return redirect(url_for("question_detail", question_id=nueva_q.id))

    return render_template("question_new.html", categories=CATEGORIAS, categorias=CATEGORIAS)


@app.route("/login", methods=["GET", "POST"], endpoint="login")
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        if not email or not password:
            flash("Por favor completá todos los campos.", "error")
            return redirect(url_for("index", tab="login"))

        nombre = email.split("@")[0].replace(".", " ").title() if "@" in email else "Usuario"
        rol = "admin" if "admin" in email.lower() else "usuario"
        session["user"] = {
            "id": 1,
            "name": nombre,
            "nombre": nombre,
            "email": email,
            "role": rol,
            "rol": rol,
            "reputation": 150,
            "reputacion": 150,
            "questions_count": 2,
            "preguntas_count": 2,
            "answers_count": 5,
            "respuestas_count": 5,
        }
        flash(f"¡Bienvenido de nuevo, {nombre}!", "success")
        return redirect(url_for("home"))
    return render_template("auth/auth.html", active_tab="login")


@app.route("/registro", methods=["GET", "POST"], endpoint="register")
def register():
    if request.method == "POST":
        nombre = (request.form.get("name") or request.form.get("nombre", "")).strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        rol = request.form.get("role") or request.form.get("rol", "usuario")

        if not nombre or not email or not password:
            flash("Por favor completá todos los campos obligatorios.", "error")
            return redirect(url_for("index", tab="register"))

        session["user"] = {
            "id": random.randint(10, 999),
            "name": nombre,
            "nombre": nombre,
            "email": email,
            "role": rol,
            "rol": rol,
            "reputation": 0,
            "reputacion": 0,
            "questions_count": 0,
            "preguntas_count": 0,
            "answers_count": 0,
            "respuestas_count": 0,
        }
        flash(f"Cuenta creada exitosamente. ¡Bienvenido, {nombre}!", "success")
        return redirect(url_for("home"))
    return render_template("auth/auth.html", active_tab="register")


@app.route("/logout", endpoint="logout")
def logout():
    session.clear()
    flash("Sesión cerrada correctamente.", "info")
    return redirect(url_for("index"))


@app.route("/usuario/<int:user_id>")
def profile(user_id):
    usuario = mock_user(user_id, "GUASA!", "admin")
    usuario.tipo = "Usuario"
    usuario.fecha_registro = datetime(2024, 1, 10)
    usuario.preguntas_count = 12
    usuario.respuestas_count = 34
    usuario.reputacion = 1420

    preguntas_u = SAMPLE_QUESTIONS[:4]
    respuestas_u = [
        mock_respuesta(10, "Esta es una respuesta de ejemplo del usuario.", es_aceptada=True, votos=15),
        mock_respuesta(11, "Aquí otra respuesta con buen puntaje.", votos=7),
    ]
    for r in respuestas_u:
        r.autor.tipo = "Usuario"
        r.autor.getNombreVisible = lambda: "Valentín Tello"

    return render_template("user/profile.html",
        usuario=usuario,
        preguntas=preguntas_u,
        respuestas=respuestas_u,
        votos=[],
    )


@app.route("/admin")
def admin_dashboard():
    usuarios = [mock_user(i, f"Usuario {i}", random.choice(["usuario", "moderador", "admin"])) for i in range(1, 9)]
    ai_config_obj = type("C", (), {
        "provider": "openai",
        "umbral_horas": 24,
        "timeout": 60,
        "enabled": True,
    })()
    return render_template("admin/dashboard.html",
        stats=STATS,
        usuarios=usuarios,
        preguntas_recientes=SAMPLE_QUESTIONS,
        ai_config=ai_config_obj,
    )


@app.route("/admin/config-ia", methods=["POST"])
def admin_config_ai():
    return redirect(url_for("admin_dashboard"))


@app.route("/categorias")
def categories():
    return render_template("categories.html",
        categorias=CATEGORIAS,
        tags=TAGS,
        stats=STATS,
    )


@app.route("/preguntas/<int:question_id>/responder", methods=["POST"])
def answer_create(question_id):
    return redirect(url_for("question_detail", question_id=question_id))


@app.route("/respuestas/<int:answer_id>/eliminar")
def answer_delete(answer_id):
    return redirect(url_for("home"))


@app.route("/preguntas/<int:question_id>/eliminar")
def question_delete(question_id):
    return redirect(url_for("home"))


@app.route("/preguntas/<int:question_id>/editar")
def question_edit(question_id):
    return redirect(url_for("question_detail", question_id=question_id))


@app.route("/perfil/foto", methods=["POST"], endpoint="profile_photo_upload")
def profile_photo_upload():
    cur = get_current_user()
    if not cur:
        flash("Debes iniciar sesión para cambiar tu foto.", "error")
        return redirect(url_for("login"))

    file = request.files.get("avatar")
    if file and file.filename:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in [".png", ".jpg", ".jpeg", ".webp"]:
            ext = ".png"
        filename = f"user_{cur.id}{ext}"
        filepath = os.path.join(AVATARS_FOLDER, filename)
        file.save(filepath)
        flash("¡Foto de perfil actualizada exitosamente!", "success")
    else:
        flash("No se seleccionó ninguna imagen válida.", "error")

    return redirect(url_for("profile", user_id=cur.id))


# ─── Run ────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\nQAI Dev Server")
    print("─" * 40)
    print("  http://localhost:5000          → Login / Registro (Página principal)")
    print("  http://localhost:5000/home     → Home / Feed de preguntas")
    print("  http://localhost:5000/preguntas/1  → Detalle")
    print("  http://localhost:5000/preguntas/nueva → Nueva pregunta")
    print("  http://localhost:5000/login    → Login")
    print("  http://localhost:5000/registro → Registro")
    print("  http://localhost:5000/usuario/1 → Perfil")
    print("  http://localhost:5000/admin    → Panel admin")
    print("  http://localhost:5000/categorias → Categorías")
    print("─" * 40)
    app.run(debug=True, port=5000)
