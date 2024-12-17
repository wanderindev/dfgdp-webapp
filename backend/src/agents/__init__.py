from flask import Blueprint

agents_bp = Blueprint("agents", __name__)

from . import models
