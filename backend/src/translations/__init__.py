from flask import Blueprint

translations_bp = Blueprint("translations", __name__)

from . import models

# from . import views
