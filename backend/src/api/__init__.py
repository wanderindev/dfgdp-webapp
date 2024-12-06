from flask import Blueprint

api_bp = Blueprint('api', __name__)

from . import views  # This will contain our API routes