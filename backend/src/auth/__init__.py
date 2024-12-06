from flask import Blueprint

auth_bp = Blueprint('auth', __name__)

from . import views  # This will contain login/logout routes
from . import models  # This will contain the User model