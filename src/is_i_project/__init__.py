import os

from flask import Flask

from is_i_project import models as _models  # noqa: F401
from is_i_project.api import register_api
from is_i_project.config import config
from is_i_project.extensions import db
from is_i_project.web import register_web


def create_app(config_name: str | None = None) -> Flask:
    app = Flask(__name__)

    resolved_config = config_name or os.getenv('APP_ENV', 'development')
    app.config.from_object(config[resolved_config]())
    db.init_app(app)

    if not app.config.get('TESTING'):
        with app.app_context():
            db.create_all()

    register_api(app)
    register_web(app)

    return app
