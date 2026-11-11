# 📡 Especificación de Endpoints y Requerimientos de Backend (Front ↔ Back)

Este documento detalla todas las rutas, endpoints de API REST y variables de contexto que el **frontend** necesita del **backend** Flask para funcionar de manera integrada.

---

## 1. ⚡ Endpoints API REST (Llamadas Asíncronas / JSON vía `fetch`)

Estas rutas son consumidas por el script de cliente (`static/js/main.js`) sin recargar la página:

### 1.1 Votación de Preguntas y Respuestas
* **Endpoint:** `POST /api/questions/<int:id>/vote`  
* **Endpoint:** `POST /api/answers/<int:id>/vote`  
* **Headers:** `Content-Type: application/json`
* **Payload Request:**
  ```json
  {
    "direction": "up" // "up" para voto positivo, "down" para voto negativo
  }
  ```
* **Respuesta esperada (200 OK):**
  ```json
  {
    "status": "success",
    "new_score": 15
  }
  ```

---

### 1.2 Aceptar Respuesta como Solución
* **Endpoint:** `POST /api/answers/<int:id>/accept`  
* **Descripción:** Marca la respuesta como la aceptada por el autor de la pregunta (desmarcando cualquier otra previa).
* **Respuesta esperada (200 OK):**
  ```json
  {
    "status": "success",
    "accepted_answer_id": 12
  }
  ```

---

### 1.3 Modificar Rol de Usuario (Panel Admin)
* **Endpoint:** `PATCH /api/admin/users/<int:user_id>/role`  
* **Headers:** `Content-Type: application/json`
* **Payload Request:**
  ```json
  {
    "role": "admin" // Valores válidos: "usuario", "moderador", "admin"
  }
  ```
* **Respuesta esperada (200 OK):**
  ```json
  {
    "status": "success",
    "user_id": 3,
    "new_role": "admin"
  }
  ```

---

## 2. 🌐 Rutas Web / Vistas HTML (`url_for(...)`)

Estas son las rutas tradicionales que procesan navegación y envío de formularios estándar de Flask:

### 2.1 Preguntas y Respuestas
| Nombre `url_for` | Método HTTP | Ruta Sugerida | Descripción / Campos esperados |
|---|---|---|---|
| `home` | `GET` | `/` | Feed principal. Filtros vía query params: `?categoria=<str>`, `?tag=<str>`, `?q=<str>`. |
| `question_detail` | `GET` | `/preguntas/<int:question_id>` | Detalle de pregunta y sus respuestas. |
| `question_new` | `GET`, `POST` | `/preguntas/nueva` | **GET:** Renderiza formulario.<br>**POST:** Procesa campos `titulo`, `cuerpo`, `categoria`, `tags` (string separado por comas), `solicitar_ia` (opcional: `"1"`), `ai_provider` (`"openai"`, `"gemini"`, `"local"`). |
| `question_edit` | `GET`, `POST` | `/preguntas/<int:question_id>/editar` | Edición de la pregunta por su autor. |
| `question_delete` | `POST` / `GET` | `/preguntas/<int:question_id>/eliminar` | Elimina la pregunta indicada. |
| `answer_create` | `POST` | `/preguntas/<int:question_id>/responder` | Procesa nueva respuesta. Campo: `cuerpo`. |
| `answer_delete` | `POST` / `GET` | `/respuestas/<int:answer_id>/eliminar` | Elimina una respuesta por su autor o admin. |

---

### 2.2 Autenticación y Cuentas
| Nombre `url_for` | Método HTTP | Ruta Sugerida | Descripción / Campos esperados |
|---|---|---|---|
| `login` | `GET`, `POST` | `/login` | **POST:** `email`, `password`, `remember_me` (opcional). |
| `register` | `GET`, `POST` | `/registro` | **POST:** `nombre`, `email`, `password`, `password_confirm`. |
| `logout` | `GET` / `POST` | `/logout` | Cierra la sesión activa. |
| `forgot_password` | `GET`, `POST` | `/recuperar-contrasena` | Recuperación o reseteo de contraseña. |
| `profile` | `GET` | `/usuario/<int:user_id>` | Perfil público e historial del usuario. |
| `profile_edit` | `GET`, `POST` | `/perfil/editar` | Formulario para editar datos personales. |

---

### 2.3 Administración y Clasificación
| Nombre `url_for` | Método HTTP | Ruta Sugerida | Descripción / Campos esperados |
|---|---|---|---|
| `categories` | `GET` | `/categorias` | Vista general de categorías y nube de tags. |
| `admin_dashboard` | `GET` | `/admin` | Panel de control (métricas, usuarios, moderación de preguntas). |
| `admin_config_ai` | `POST` | `/admin/config-ia` | **POST:** `ai_provider`, `umbral_horas`, `timeout_segundos`, `ai_enabled` (checkbox). |
| `admin_delete_user` | `POST` / `GET` | `/admin/usuarios/<int:user_id>/eliminar` | Eliminación de usuario por administrador. |

---

## 3. 🧩 Variables de Contexto Globales (Inyectadas en Jinja2)

Para evitar errores en `base.html` y en el navbar común, configurar un `@app.context_processor` en Flask que inyecte:

```python
@app.context_processor
def inject_globals():
    return {
        # Objeto del usuario autenticado actual o None si es anónimo
        # Atributos esperados: .id, .nombre, .email, .rol ('usuario'|'moderador'|'admin'), .reputacion
        "current_user": current_user, 
        
        # Función o helper para protección CSRF
        "csrf_token": generate_csrf_token,
        
        # Entero con cantidad de preguntas sin responder (para el badge de la barra lateral)
        "unanswered_count": count_unanswered_questions(),
    }
```

---

## 4. 📦 Variables esperadas por cada plantilla (`render_template`)

### `home.html`
* `questions`: Lista de objetos `Pregunta` (con atributos: `.id`, `.titulo`, `.cuerpo`, `.categoria`, `.tags`, `.votos`, `.respuestas_count`, `.tiene_aceptada`, `.tiene_respuesta_ia`, `.fecha_publicacion`, `.autor`).
* `stats`: Diccionario con:
  * `total_preguntas`, `total_respuestas`, `total_usuarios`, `respuestas_ia`.
* `categorias_populares`: Lista de categorías principales con `.nombre` y `.count`.
* `top_usuarios`: Lista de usuarios con mayor reputación con `.id`, `.nombre`, `.reputacion`.
* `tags_populares`: Lista de tags frecuentes con `.nombre`.
* `pagination` *(opcional)*: Objeto con `.pages`, `.page`, `.has_prev`, `.has_next`, `.iter_pages()`.

### `question_detail.html`
* `pregunta`: Objeto `Pregunta` (incluyendo `.puntuacion`, `.vistas`, `.autor`, `.categoria`, `.tags`).
* `respuestas`: Lista de objetos `Respuesta` (con `.id`, `.cuerpo`, `.puntuacion`, `.es_aceptada`, `.fecha_publicacion`, `.autor`, `.user_vote`).
  * Si el autor es IA: `.autor.tipo == 'IA'`, `.autor.nombreModelo`, `.autor.getNombreVisible()`.
* `user_vote`: Entero con el voto del usuario actual (`1`, `-1` o `0`).
* `preguntas_similares`: Lista de preguntas sugeridas para el sidebar.

### `question_new.html`
* `categorias`: Lista de objetos categoría (`.nombre`, `.descripcion`).

### `user/profile.html`
* `usuario`: Objeto `Usuario` con `.id`, `.nombre`, `.email`, `.rol`, `.reputacion`, `.fecha_registro`, `.preguntas_count`, `.respuestas_count`.
* `preguntas`: Lista de preguntas creadas por el usuario.
* `respuestas`: Lista de respuestas dadas por el usuario.
* `votos`: Lista de votos emitidos por el usuario (con `.publicacion`, `.es_positivo`, `.fecha`).

### `admin/dashboard.html`
* `stats`: Métricas (`total_usuarios`, `total_preguntas`, `total_respuestas`, `respuestas_ia`, `nuevos_usuarios_semana`, `pct_ia`, etc.).
* `usuarios`: Lista de todos los usuarios para la tabla de gestión.
* `preguntas_recientes`: Lista de preguntas recientes para moderación.
* `ai_config`: Objeto o dict con configuración actual del modelo (`.provider`, `.umbral_horas`, `.timeout`, `.enabled`).

### `categories.html`
* `categorias`: Lista completa de categorías con `.nombre`, `.descripcion`, `.count`, `.respondidas`.
* `tags`: Lista de tags con `.nombre`, `.count` para el cálculo de la nube de tags.
* `stats`: Diccionario de métricas globales.
