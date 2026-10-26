import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.core.security import create_access_token, get_password_hash
from app.main import app
from app.models import Base, User, UserRole

# In-memory SQLite for high-speed, isolated unit and integration testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Fresh in-memory database per test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """TestClient that overrides the get_db dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def admin_user(db_session):
    user = User(
        email="admin@resolvex.internal",
        hashed_password=get_password_hash("AdminPass123!"),
        full_name="System Administrator",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def support_agent_user(db_session):
    user = User(
        email="agent@resolvex.internal",
        hashed_password=get_password_hash("AgentPass123!"),
        full_name="Support Agent Sarah",
        role=UserRole.SUPPORT_AGENT,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def analyst_user(db_session):
    user = User(
        email="analyst@resolvex.internal",
        hashed_password=get_password_hash("AnalystPass123!"),
        full_name="Risk Analyst Roy",
        role=UserRole.ANALYST,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_token_headers(admin_user):
    token = create_access_token(subject=admin_user.id, role=admin_user.role.value)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def support_token_headers(support_agent_user):
    token = create_access_token(subject=support_agent_user.id, role=support_agent_user.role.value)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def analyst_token_headers(analyst_user):
    token = create_access_token(subject=analyst_user.id, role=analyst_user.role.value)
    return {"Authorization": f"Bearer {token}"}
