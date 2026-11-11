from flask import Flask

from is_i_project.config import Config
from is_i_project.extensions import db

def create_app (config_class = Config) -> Flask:
    app = Flask(__name__)

    app.config.from_object(config_class)
    db.init_app(app)

    from is_i_project.api.health import health_bp
    from myapp.web.users import users_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(users_bp)

    return app
