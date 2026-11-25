# 📡 Especificación de Contrato Front ↔ Back (REST API & Vistas Web)

> **Destinado al equipo de Backend para la resolución de la [Issue #5: REST API Implementation]**  
> Este documento detalla la totalidad de los endpoints de la API REST (JSON), las rutas de vistas web (HTML) y la estructura de datos en inglés que el frontend consume y produce.

---

## 1. ⚡ Especificación de la REST API (JSON) — Criterios de Aceptación Issue #5

Todos los endpoints REST devuelven respuestas en formato JSON acompañadas de su respectivo código de estado HTTP (`200 OK`, `201 Created`, `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`).

### 1.1 Preguntas (`/api/questions`)

#### `GET /api/questions`
* **Descripción:** Lista preguntas con paginación y filtros opcionales.
* **Query Params:**
  * `category` (string, opcional): Filtrar por nombre de categoría.
  * `tag` (string, opcional): Filtrar por tag.
  * `q` (string, opcional): Búsqueda por texto en título/cuerpo.
  * `filter` (string, opcional): `all` (recientes), `top` (más votadas), `unanswered` (sin respuesta), `ai` (con respuesta de IA).
  * `page` (int, default: 1), `per_page` (int, default: 10).
* **Respuesta esperada (200 OK):**
  ```json
  {
    "status": "success",
    "total": 42,
    "page": 1,
    "pages": 5,
    "questions": [
      {
        "id": 1,
        "title": "¿Cómo implementar el patrón Strategy en Python con SQLAlchemy?",
        "body": "<p>Detalle de la pregunta...</p>",
        "category": "Backend",
        "tags": ["python", "sqlalchemy", "patterns"],
        "score": 15,
        "answers_count": 3,
        "has_accepted": true,
        "has_ai_response": false,
        "views": 120,
        "post_date": "2026-11-20T14:30:00Z",
        "author": {
          "id": 2,
          "name": "Valentín Tello",
          "reputation": 350,
          "avatar_url": "/static/uploads/avatars/user_2.png"
        }
      }
    ]
  }
  ```

#### `GET /api/questions/<int:id>`
* **Descripción:** Retorna el detalle completo de una pregunta y todas sus respuestas.
* **Respuesta esperada (200 OK):**
  ```json
  {
    "status": "success",
    "question": {
      "id": 1,
      "title": "¿Cómo implementar el patrón Strategy?",
      "body": "<p>Contenido completo...</p>",
      "category": "Backend",
      "tags": ["python", "flask"],
      "score": 15,
      "views": 121,
      "post_date": "2026-11-20T14:30:00Z",
      "user_vote": 1,
      "author": {
        "id": 2,
        "name": "Valentín Tello",
        "reputation": 350,
        "avatar_url": "/static/uploads/avatars/user_2.png"
      },
      "answers": [
        {
          "id": 5,
          "body": "<p>Para implementar Strategy...</p>",
          "score": 8,
          "accepted": true,
          "user_vote": 0,
          "post_date": "2026-11-20T16:00:00Z",
          "author": {
            "id": 10,
            "name": "Román Maldonado",
            "type": "User",
            "reputation": 1200,
            "avatar_url": "/static/uploads/avatars/user_10.png"
          }
        },
        {
          "id": 6,
          "body": "<p>Respuesta generada automáticamente...</p>",
          "score": 2,
          "accepted": false,
          "user_vote": 0,
          "post_date": "2026-11-20T18:00:00Z",
          "author": {
            "id": 999,
            "name": "AutorIA",
            "type": "AI",
            "modelName": "GPT-4o",
            "reputation": 0
          }
        }
      ]
    }
  }
  ```

#### `POST /api/questions`
* **Descripción:** Crea una nueva pregunta.
* **Payload Request:**
  ```json
  {
    "title": "Error al conectar Flask con SQLAlchemy",
    "body": "No logra instanciar el pool de conexiones...",
    "category": "Backend",
    "tags": ["flask", "sqlalchemy"],
    "request_ai": true,
    "ai_provider": "openai"
  }
  ```
* **Respuesta esperada (201 Created):**
  ```json
  {
    "status": "success",
    "message": "Pregunta creada exitosamente",
    "question_id": 12
  }
  ```

#### `PUT /api/questions/<int:id>`
* **Descripción:** Edita una pregunta existente (solo autor o admin).
* **Payload Request:**
  ```json
  {
    "title": "Nuevo título corregido",
    "body": "Nuevo cuerpo detallado...",
    "category": "Backend",
    "tags": ["flask", "orm"]
  }
  ```
* **Respuesta esperada (200 OK):**
  ```json
  {
    "status": "success",
    "message": "Pregunta actualizada"
  }
  ```

#### `DELETE /api/questions/<int:id>`
* **Descripción:** Elimina una pregunta y sus respuestas asociadas.
* **Respuesta esperada (200 OK):**
  ```json
  {
    "status": "success",
    "message": "Pregunta eliminada"
  }
  ```

#### `POST /api/questions/<int:id>/vote`
* **Descripción:** Emite o retira un voto positivo/negativo en una pregunta.
* **Payload Request:**
  ```json
  {
    "direction": "up" // "up" para voto positivo (+1), "down" para negativo (-1)
  }
  ```
* **Respuesta esperada (200 OK):**
  ```json
  {
    "status": "success",
    "new_score": 16,
    "user_vote": 1
  }
  ```

---

### 1.2 Respuestas (`/api/answers`)

#### `POST /api/questions/<int:question_id>/answers`
* **Descripción:** Agrega una respuesta a la pregunta indicada.
* **Payload Request:**
  ```json
  {
    "body": "Esta es la solución al problema..."
  }
  ```
* **Respuesta esperada (201 Created):**
  ```json
  {
    "status": "success",
    "answer_id": 23,
    "message": "Respuesta publicada"
  }
  ```

#### `DELETE /api/answers/<int:id>`
* **Descripción:** Elimina una respuesta (autor o admin).
* **Respuesta esperada (200 OK):**
  ```json
  {
    "status": "success",
    "message": "Respuesta eliminada"
  }
  ```

#### `POST /api/answers/<int:id>/vote`
* **Payload Request:**
  ```json
  {
    "direction": "up"
  }
  ```
* **Respuesta esperada (200 OK):**
  ```json
  {
    "status": "success",
    "new_score": 9,
    "user_vote": 1
  }
  ```

#### `POST /api/answers/<int:id>/accept`
* **Descripción:** Marca la respuesta como solución aceptada (solo autor de la pregunta).
* **Respuesta esperada (200 OK):**
  ```json
  {
    "status": "success",
    "accepted_answer_id": 23
  }
  ```

---

### 1.3 Categorías y Tags

#### `GET /api/categories`
* **Respuesta esperada (200 OK):**
  ```json
  {
    "status": "success",
    "categories": [
      {
        "id": 1,
        "name": "Backend",
        "description": "Flask, Django, APIs REST, bases de datos y más.",
        "count": 28,
        "answered_count": 14
      }
    ]
  }
  ```

#### `GET /api/tags`
* **Respuesta esperada (200 OK):**
  ```json
  {
    "status": "success",
    "tags": [
      { "id": 1, "name": "python", "count": 42 },
      { "id": 2, "name": "flask", "count": 38 }
    ]
  }
  ```

---

### 1.4 Usuarios

#### `GET /api/users/<int:id>`
* **Respuesta esperada (200 OK):**
  ```json
  {
    "status": "success",
    "user": {
      "id": 1,
      "name": "Valentín Tello",
      "email": "valentin.tello@example.com",
      "role": "admin",
      "reputation": 350,
      "registered_at": "2024-03-15T00:00:00Z",
      "avatar_url": "/static/uploads/avatars/user_1.png",
      "questions_count": 8,
      "answers_count": 14
    }
  }
  ```

---

## 2. 🌐 Vistas Web y Navegación HTML (`url_for(...)`)

Estas rutas renderizan las plantillas Jinja2 y procesan formularios tradicionales:

| Endpoint `url_for` | Método | Ruta HTTP | Plantilla asociada | Descripción / Campos esperados |
|---|---|---|---|---|
| `home` | `GET` | `/` y `/home` | `home.html` | Feed de preguntas. Acepta query params `?category=`, `?tag=`, `?q=`, `?filter=`. |
| `question_detail` | `GET` | `/preguntas/<int:question_id>` | `question_detail.html` | Hilo con pregunta y sus respuestas. |
| `question_new` | `GET`, `POST` | `/preguntas/nueva` | `question_new.html` | **POST:** `title`, `body`, `category`, `tags` (string separado por comas), `request_ai` (opcional: `"1"`), `ai_provider`. |
| `question_edit` | `GET`, `POST` | `/preguntas/<int:question_id>/editar` | `question_new.html` | Edición de la pregunta por su autor. |
| `question_delete` | `POST` / `GET` | `/preguntas/<int:question_id>/eliminar` | Redirección a `home` | Elimina la pregunta. |
| `answer_create` | `POST` | `/preguntas/<int:question_id>/responder` | Redirección a hilo | **POST:** `body`. |
| `answer_delete` | `POST` / `GET` | `/respuestas/<int:answer_id>/eliminar` | Redirección a hilo | Elimina una respuesta. |
| `profile` | `GET` | `/usuario/<int:user_id>` | `user/profile.html` | Perfil público y pestañas de actividad. |
| `profile_photo_upload` | `POST` | `/perfil/foto` | Redirección a perfil | Subida de archivo de imagen `multipart/form-data` campo `avatar`. Se guarda en `static/uploads/avatars/user_<id>.<ext>`. |
| `login` | `GET`, `POST` | `/login` | `auth/auth.html` | **POST:** `email`, `password`. |
| `register` | `GET`, `POST` | `/registro` | `auth/auth.html` | **POST:** `name`, `email`, `password`, `role`. |
| `logout` | `GET`, `POST` | `/logout` | Redirección a login | Destruye la sesión de usuario. |
| `categories` | `GET` | `/categorias` | `categories.html` | Grilla de categorías y nube de tags. |
| `admin_dashboard` | `GET` | `/admin` | `admin/dashboard.html` | Panel admin con visualización de usuarios, moderación de preguntas y config IA. |
| `admin_config_ai` | `POST` | `/admin/config-ia` | Redirección admin | **POST:** `ai_provider`, `umbral_horas`, `timeout_segundos`, `ai_enabled`. |

---

## 3. 🧩 Variables de Contexto Globales (Inyectadas en Jinja2)

Para asegurar el correcto funcionamiento del navbar, layouts y el sidebar, Flask debe registrar este `@app.context_processor`:

```python
@app.context_processor
def inject_globals():
    return {
        # Objeto del usuario autenticado actual o None si es anónimo
        # Atributos esperados: .id, .name, .email, .role, .reputation, .avatar_url
        "current_user": current_user, 
        
        # Función o helper para protección CSRF en formularios
        "csrf_token": generate_csrf_token,
        
        # Entero con cantidad de preguntas sin responder (para el badge del sidebar)
        "unanswered_count": count_unanswered_questions(),
    }
```

---

## 4. 📦 Nombres de Atributos Esperados por las Plantillas (En Inglés)

| Entidad | Atributos esperados por el frontend |
|---|---|
| **Question** | `id`, `title`, `body`, `category`, `tags`, `score`, `views`, `answers_count`, `has_accepted`, `has_ai_response`, `post_date`, `author` (objeto usuario). |
| **Response** | `id`, `body`, `score`, `accepted`, `post_date`, `author` (usuario o bot IA), `user_vote`. |
| **User** | `id`, `name`, `email`, `role`, `reputation`, `registered_at` / `post_date`, `avatar_url`, `questions_count`, `answers_count`. |
| **Category** | `id`, `name`, `description`, `count`, `answered_count`. |
| **Tag** | `id`, `name`, `count`. |
| **Stats (Globales)** | `total_users`, `total_questions`, `total_answers`, `ai_answers`, `new_users_week`, `new_questions_week`, `new_answers_week`, `pct_ia`. |
