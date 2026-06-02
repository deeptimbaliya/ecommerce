import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base, get_db
from main import app
from unittest.mock import patch
from app.models.user import User


SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"


engine= create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

TestingSessionLocal=sessionmaker(
    autocommit=False,
    autoflush=False,
    bind= engine
)

@pytest.fixture(autouse=True)          # ✅ applies to ALL tests automatically
def mock_celery_tasks():
    """Prevent Celery from connecting to Redis during tests."""
    with patch("app.tasks.sendEmail.send_welcome_email.delay") as mock1, \
         patch("app.tasks.sendEmail.send_password_reset_email.delay") as mock2:
        yield {"welcome": mock1, "reset": mock2}

@pytest.fixture(scope ="function")
def db():
    Base.metadata.create_all(bind=engine)
    session= TestingSessionLocal()
    try:
        yield session
    finally :
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope ="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally : 
            db.close()

    app.dependency_overrides[get_db]=override_get_db
    with TestClient(app) as c :
        yield c
    app.dependency_overrides.clear()

@pytest.fixture(scope ="function")
def test_user_data():
    return {
        "name": "Test User",
        "email": "test@example.com",
        "password": "Test@1234",
        "confirm_password": "Test@1234",
        "role": "user"
    }

@pytest.fixture
def registered_user(client, test_user_data):
    """A user that's already registered."""
    response = client.post("/api/v1/auth/register", json=test_user_data)
    assert response.status_code == 201
    return response.json()["data"]


@pytest.fixture
def auth_token(client, test_user_data, registered_user):
    """A valid JWT token for the test user."""
    response = client.post("/api/v1/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def auth_headers(auth_token):
    """Authorization headers ready to use."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def admin_user(client, db):
    """An admin user for testing protected routes."""
    from app.models.user import User
    from app.core.security import hash_password

    admin = User(
        name="Admin User",
        email="admin@example.com",
        password_hash=hash_password("Admin@1234"),
        role="admin"
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)

    # get token
    response = client.post("/api/v1/auth/login", json={
        "email": "admin@example.com",
        "password": "Admin@1234"
    })
    token = response.json()["access_token"]
    return {"user": admin, "headers": {"Authorization": f"Bearer {token}"}}