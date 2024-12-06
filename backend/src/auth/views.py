from datetime import datetime, timezone

from flask import jsonify, request
from flask_login import login_user, logout_user, login_required, current_user

from . import auth_bp
from .models import User, db


@auth_bp.route("/login", methods=["POST"])
def login():
    """Handle user login."""
    if current_user.is_authenticated:
        return jsonify({"message": "Already logged in"}), 400

    data = request.get_json()
    if not data or not data.get("email") or not data.get("password"):
        return jsonify({"message": "Missing email or password"}), 400

    user = User.query.filter_by(email=data["email"]).first()
    if user and user.check_password(data["password"]):
        if not user.active:
            return jsonify({"message": "Account is deactivated"}), 403

        login_user(user, remember=data.get("remember", False))
        user.last_login_at = datetime.now(timezone.utc)
        db.session.commit()

        return jsonify(
            {
                "message": "Logged in successfully",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "full_name": user.full_name,
                },
            }
        )

    return jsonify({"message": "Invalid email or password"}), 401


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    """Handle user logout."""
    logout_user()
    return jsonify({"message": "Logged out successfully"})


@auth_bp.route("/me", methods=["GET"])
@login_required
def get_current_user():
    """Get current user information."""
    return jsonify(
        {
            "user": {
                "id": current_user.id,
                "email": current_user.email,
                "full_name": current_user.full_name,
            }
        }
    )
