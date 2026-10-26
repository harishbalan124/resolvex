from fastapi import status
from app.models.audit_log import AuditLog
from app.models.user import User


def test_admin_can_list_users(client, admin_token_headers):
    response = client.get("/api/v1/users/", headers=admin_token_headers)
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1


def test_admin_can_create_user(client, admin_token_headers, db_session):
    payload = {
        "email": "new.analyst@resolvex.internal",
        "full_name": "New Risk Analyst",
        "role": "ANALYST",
        "password": "Password999!",
        "is_active": True,
    }
    response = client.post("/api/v1/users/", json=payload, headers=admin_token_headers)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["email"] == payload["email"]
    assert data["role"] == "ANALYST"
    assert "password" not in data
    assert "hashed_password" not in data

    # Check audit log entry
    audit = db_session.query(AuditLog).filter(AuditLog.action == "USER_CREATED").first()
    assert audit is not None
    assert str(data["id"]) in audit.details


def test_support_agent_cannot_access_user_management(client, support_token_headers):
    # GET /users
    response = client.get("/api/v1/users/", headers=support_token_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "Operation not permitted" in response.json()["detail"]

    # POST /users
    payload = {
        "email": "hacked@resolvex.internal",
        "full_name": "Hacked Agent",
        "role": "ADMIN",
        "password": "Password999!",
    }
    response = client.post("/api/v1/users/", json=payload, headers=support_token_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_analyst_cannot_access_user_management(client, analyst_token_headers):
    # GET /users
    response = client.get("/api/v1/users/", headers=analyst_token_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "Operation not permitted" in response.json()["detail"]


def test_unauthenticated_request_rejected(client):
    response = client.get("/api/v1/users/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
