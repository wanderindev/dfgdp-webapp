from datetime import datetime, timezone
from typing import Tuple

from flask import jsonify, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.wrappers import Response

from . import auth_bp
from .models import User, db


@auth_bp.route("/login", methods=["POST"])
def login() -> Tuple[Response, int]:
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

        return (
            jsonify(
                {
                    "message": "Logged in successfully",
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "full_name": user.full_name,
                    },
                }
            ),
            200,
        )

    return jsonify({"message": "Invalid email or password"}), 401


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout() -> Tuple[Response, int]:
    """Handle user logout."""
    logout_user()
    return jsonify({"message": "Logged out successfully"}), 200


@auth_bp.route("/me", methods=["GET"])
@login_required
def get_current_user() -> Response:
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


@auth_bp.route("/api/users", methods=["GET"])
@login_required
def list_users() -> Response:
    """Get paginated list of users with optional filtering."""
    # Get query parameters
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    email_filter = request.args.get("email", "")

    # Build query
    query = User.query

    # Apply filters
    if email_filter:
        query = query.filter(User.email.ilike(f"%{email_filter}%"))

    # Execute query with pagination
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    # Format response
    users = [
        {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "active": user.active,
            "last_login_at": user.last_login_at.isoformat()
            if user.last_login_at
            else None,
        }
        for user in pagination.items
    ]

    return jsonify(
        {
            "users": users,
            "total": pagination.total,
            "pages": pagination.pages,
            "current_page": page,
        }
    )


@auth_bp.route("/api/users/<int:user_id>", methods=["PUT"])
@login_required
def update_user(user_id: int) -> Tuple[Response, int]:
    """Update user details."""
    user = User.query.get_or_404(user_id)
    data = request.get_json()

    if not data:
        return jsonify({"message": "No data provided"}), 400

    # Update allowed fields
    if "email" in data:
        # Check if email is taken by another user
        existing = User.query.filter(
            User.email == data["email"], User.id != user_id
        ).first()
        if existing:
            return jsonify({"message": "Email already taken"}), 400
        user.email = data["email"]

    if "full_name" in data:
        user.full_name = data["full_name"]

    try:
        db.session.commit()
        return (
            jsonify(
                {
                    "message": "User updated successfully",
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "full_name": user.full_name,
                        "active": user.active,
                    },
                }
            ),
            200,
        )
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500


@auth_bp.route("/api/users/<int:user_id>/activate", methods=["POST"])
@login_required
def activate_user(user_id: int) -> Tuple[Response, int]:
    """Activate a user account."""
    user = User.query.get_or_404(user_id)

    if user.active:
        return jsonify({"message": "User is already active"}), 400

    try:
        user.active = True
        db.session.commit()
        return (
            jsonify(
                {
                    "message": "User activated successfully",
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "full_name": user.full_name,
                        "active": user.active,
                    },
                }
            ),
            200,
        )
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500


@auth_bp.route("/api/users/<int:user_id>/deactivate", methods=["POST"])
@login_required
def deactivate_user(user_id: int) -> Tuple[Response, int]:
    """Deactivate a user account."""
    user = User.query.get_or_404(user_id)

    # Prevent deactivating own account
    if user.id == current_user.id:
        return jsonify({"message": "Cannot deactivate own account"}), 400

    if not user.active:
        return jsonify({"message": "User is already inactive"}), 400

    try:
        user.active = False
        db.session.commit()
        return (
            jsonify(
                {
                    "message": "User deactivated successfully",
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "full_name": user.full_name,
                        "active": user.active,
                    },
                }
            ),
            200,
        )
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500


@auth_bp.route("/api/users/<int:user_id>/reset-password", methods=["POST"])
@login_required
def reset_user_password(user_id: int) -> Tuple[Response, int]:
    """Reset a user's password."""
    user = User.query.get_or_404(user_id)
    data = request.get_json()

    if not data or "password" not in data:
        return jsonify({"message": "Password is required"}), 400

    try:
        user.set_password(data["password"])
        db.session.commit()
        return (
            jsonify(
                {
                    "message": "Password reset successfully",
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "full_name": user.full_name,
                        "active": user.active,
                    },
                }
            ),
            200,
        )
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500
