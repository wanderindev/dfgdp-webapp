from flask import Blueprint

tasks_bp = Blueprint("tasks", __name__)

from . import views, tasks, worker
