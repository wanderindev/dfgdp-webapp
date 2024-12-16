from typing import Optional

from flask import Flask, g, request, current_app

from translations.models import ApprovedLanguage


# noinspection PyUnresolvedReferences
class LanguageMiddleware:
    """Middleware to handle language selection for requests"""

    def __init__(self, app: Optional[Flask] = None) -> None:
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        """Initialize the middleware with a Flask application"""
        self.app = app

        @app.before_request
        def set_language():
            """
            Set language for request based on URL or header.
            Called before each request.
            """
            try:
                # First check URL path for language code
                path_parts = request.path.split("/")
                if len(path_parts) > 1:
                    potential_lang = path_parts[1]
                    if LanguageMiddleware._is_valid_language(potential_lang):
                        g.language = potential_lang
                        return

                # Check Accept-Language header
                accept_languages = request.accept_languages
                if accept_languages:
                    # Get list of active language codes
                    active_langs = [
                        lang.code for lang in ApprovedLanguage.get_active_languages()
                    ]
                    best_match = accept_languages.best_match(active_langs)
                    if best_match:
                        g.language = best_match
                        return

                # Fallback to default language
                default_lang = ApprovedLanguage.get_default_language()
                g.language = default_lang.code if default_lang else "en"

            except Exception as e:
                # Log the error but don't fail the request
                current_app.logger.error(f"Error in language middleware: {str(e)}")
                # Set English as ultimate fallback
                g.language = "en"

    @staticmethod
    def _is_valid_language(lang_code: str) -> bool:
        """Check if a language code is valid and active"""
        try:
            lang = ApprovedLanguage.query.filter_by(
                code=lang_code, is_active=True
            ).first()
            return lang is not None
        except Exception as e:
            current_app.logger.error(f"Error checking language validity: {str(e)}")
            return False
