import os
from datetime import timedelta
from typing import Dict, Type, Set, Optional

from dotenv import load_dotenv

load_dotenv()


class BaseConfig:
    """Base configuration."""

    BASE_DIR: str = os.path.abspath(os.path.dirname(__file__))
    print(f"BASE_DIR: {BASE_DIR}")

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key")

    # Database
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_DATABASE_URI: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@db:5432/dfgdp_webapp",
    )

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6373/0")

    # API Keys
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")

    # JWT Settings
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "jwt-secret-key")
    JWT_ACCESS_TOKEN_EXPIRES: timedelta = timedelta(days=1)

    # Flask-Login Settings
    REMEMBER_COOKIE_DURATION: timedelta = timedelta(days=30)
    REMEMBER_COOKIE_SECURE: bool = True
    REMEMBER_COOKIE_HTTPONLY: bool = True

    # Upload Settings
    MAX_CONTENT_LENGTH: int = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER: str = os.path.join(BASE_DIR, "uploads")
    ALLOWED_IMAGE_EXTENSIONS: Set[str] = {"png", "jpg", "jpeg", "gif"}

    # Site Settings
    BLOG_URL: str = os.getenv("BLOG_URL", "https://panamaincontext.com")

    WIKIMEDIA_URL = "https://commons.wikimedia.org/w/api.php"


class DevelopmentConfig(BaseConfig):
    """Development configuration."""

    DEBUG: bool = True
    SQLALCHEMY_ECHO: bool = False
    REMEMBER_COOKIE_SECURE: bool = False  # Allow testing without HTTPS


class TestingConfig(BaseConfig):
    """Testing configuration."""

    TESTING: bool = True
    SQLALCHEMY_DATABASE_URI: str = (
        "postgresql://postgres:postgres@db:5432/dfgdp_webapp_test"
    )
    WTF_CSRF_ENABLED: bool = False
    REMEMBER_COOKIE_SECURE: bool = False


class ProductionConfig(BaseConfig):
    """Production configuration."""

    DEBUG: bool = False
    REMEMBER_COOKIE_SECURE: bool = True

    # Override with environment variables
    SQLALCHEMY_DATABASE_URI: str = os.getenv("DATABASE_URL")  # type: ignore
    REDIS_URL: str = os.getenv("REDIS_URL")  # type: ignore
    SECRET_KEY: str = os.getenv("SECRET_KEY")  # type: ignore
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY")  # type: ignore

    # Production-specific settings
    PREFERRED_URL_SCHEME: str = "https"
    SESSION_COOKIE_SECURE: bool = True
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "Lax"


config: Dict[str, Type[BaseConfig]] = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
