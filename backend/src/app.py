import os
from flask import Flask
from flask_login import LoginManager
from flask_cors import CORS

from config import config
from extensions import db, migrate, jwt, redis_client, login_manager


def create_app(config_name=None):
    """Application factory function"""
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    CORS(app)
    login_manager.init_app(app)

    # Initialize Redis
    redis_client.from_url(app.config["REDIS_URL"])

    # Register blueprints
    from auth import auth_bp
    from api import api_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(api_bp, url_prefix="/api")

    # Configure logging
    if not app.debug:
        import logging
        from logging.handlers import RotatingFileHandler

        if not os.path.exists('logs'):
            os.mkdir('logs')

        file_handler = RotatingFileHandler(
            "logs/app.log", maxBytes=10240, backupCount=10
        )
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
            )
        )
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info("Application startup")

    return app