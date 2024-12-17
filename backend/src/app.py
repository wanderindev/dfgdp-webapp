import os
from typing import Optional

from flask import Flask
from flask_cors import CORS
from flask_login import UserMixin

from auth.commands import auth_cli
from init.commands import init_cli
from config import config
from content.commands import content_cli
from extensions import db, migrate, jwt, redis_client, login_manager
from middleware.language_middleware import LanguageMiddleware
from translations.commands import translations_cli
from translations.services import register_translation_handlers


def create_app(config_name: Optional[str] = None) -> Flask:
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

    # Initialize language middleware
    LanguageMiddleware(app)

    # Register translation handlers
    register_translation_handlers()

    @login_manager.user_loader
    def load_user(user_id: str) -> Optional[UserMixin]:
        from auth.models import User

        return User.query.get(int(user_id))

    # Register blueprints
    from agents import agents_bp
    from auth import auth_bp
    from content import content_bp
    from translations import translations_bp

    app.register_blueprint(agents_bp, url_prefix="/agents")
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(content_bp, url_prefix="/content")
    app.register_blueprint(translations_bp, url_prefix="/translations")

    # Register CLI commands
    app.cli.add_command(auth_cli)
    app.cli.add_command(content_cli)
    app.cli.add_command(init_cli)
    app.cli.add_command(translations_cli)

    # Configure logging
    if not app.debug:
        import logging
        from logging.handlers import RotatingFileHandler

        if not os.path.exists("logs"):
            os.mkdir("logs")

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
