from flask import Flask

from is_i_project.config import config
from is_i_project.extensions import db

def create_app (config_name: str = None) -> Flask:
    app = Flask(__name__)

    if config_name is None:
        config_name = 'development'

    app.config.from_object(config[config_name]())
    db.init_app(app)

    # from is_i_project.api.health import health_bp
    # from myapp.web.users import users_bp
    # app.register_blueprint(health_bp)
    # app.register_blueprint(users_bp)

    print(f"CONFIGURACION OS: {config_name}")

    return app
