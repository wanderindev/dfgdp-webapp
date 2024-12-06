import json


def test_login_success(client, test_user, db_session):
    """Test successful login."""
    response = client.post(
        "/auth/login", json={"email": "test@example.com", "password": "password123"}
    )

    assert response.status_code == 200
    data = json.loads(response.data)
    assert "user" in data
    assert data["user"]["email"] == test_user.email


def test_login_invalid_credentials(client, test_user):
    """Test login with wrong password."""
    response = client.post(
        "/auth/login", json={"email": "test@example.com", "password": "wrongpassword"}
    )

    assert response.status_code == 401


def test_login_missing_fields(client):
    """Test login with missing fields."""
    response = client.post("/auth/login", json={})
    assert response.status_code == 400


def test_logout(client, test_user):
    """Test logout functionality."""
    # First login
    client.post(
        "/auth/login", json={"email": "test@example.com", "password": "password123"}
    )

    # Then logout
    response = client.post("/auth/logout")
    assert response.status_code == 200


def test_get_current_user(client, test_user):
    """Test getting current user info."""
    # First login
    client.post(
        "/auth/login", json={"email": "test@example.com", "password": "password123"}
    )

    # Get user info
    response = client.get("/auth/me")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "user" in data
    assert data["user"]["email"] == test_user.email
