import os

from flask import Flask

from is_i_project.api import register_api
from is_i_project.config import config
from is_i_project.extensions import db


def create_app(config_name: str | None = None) -> Flask:
    app = Flask(__name__)

    resolved_config = config_name or os.getenv('APP_ENV', 'development')
    app.config.from_object(config[resolved_config]())
    db.init_app(app)

    register_api(app)

    return app
