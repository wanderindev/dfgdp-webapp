from flask import Blueprint

content_bp = Blueprint("content", __name__)

from . import models

# from . import utils
# from . import views
