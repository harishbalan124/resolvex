from fastapi import status
from app.core.security import get_password_hash, verify_password
from app.models.user import User, UserRole


def test_password_hashing():
    raw_password = "SecurePassword123!"
    hashed = get_password_hash(raw_password)
    assert hashed != raw_password
    assert verify_password(raw_password, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_login_success(client, admin_user):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": admin_user.email, "password": "AdminPass123!"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["role"] == "ADMIN"
    assert data["user_id"] == admin_user.id
    assert data["full_name"] == admin_user.full_name


def test_login_invalid_password(client, admin_user):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": admin_user.email, "password": "WrongPassword!"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Incorrect email or password"


def test_login_nonexistent_user(client):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "ghost@resolvex.internal", "password": "SomePassword123!"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_login_inactive_user(client, db_session):
    inactive = User(
        email="inactive@resolvex.internal",
        hashed_password=get_password_hash("InactivePass123!"),
        full_name="Inactive Person",
        role=UserRole.SUPPORT_AGENT,
        is_active=False,
    )
    db_session.add(inactive)
    db_session.commit()

    response = client.post(
        "/api/v1/auth/login",
        data={"username": inactive.email, "password": "InactivePass123!"},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "inactive" in response.json()["detail"].lower()


def test_get_current_user_me(client, admin_token_headers, admin_user):
    response = client.get("/api/v1/auth/me", headers=admin_token_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == admin_user.email
    assert data["role"] == "ADMIN"
    assert data["id"] == admin_user.id


def test_get_current_user_unauthorized(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
