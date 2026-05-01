import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_register_user():
    response = client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "testpassword123"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["role"] == "user"


def test_register_duplicate_email():
    client.post("/auth/register", json={"email": "dup@example.com", "password": "pass123"})
    response = client.post("/auth/register", json={"email": "dup@example.com", "password": "pass123"})
    assert response.status_code == 400


def test_login_valid():
    client.post("/auth/register", json={"email": "login@example.com", "password": "pass123"})
    response = client.post("/auth/login", json={"email": "login@example.com", "password": "pass123"})
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_invalid():
    response = client.post("/auth/login", json={"email": "nobody@example.com", "password": "wrong"})
    assert response.status_code == 401


def test_get_me_authenticated():
    client.post("/auth/register", json={"email": "me@example.com", "password": "pass123"})
    login_resp = client.post("/auth/login", json={"email": "me@example.com", "password": "pass123"})
    token = login_resp.json()["access_token"]
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "me@example.com"


def test_get_me_unauthenticated():
    response = client.get("/auth/me")
    assert response.status_code == 403


def test_create_audit_unauthenticated():
    response = client.post("/audits/", json={"url": "https://example.com"})
    assert response.status_code == 403


def test_list_audits_empty():
    client.post("/auth/register", json={"email": "auditor@example.com", "password": "pass123"})
    login_resp = client.post("/auth/login", json={"email": "auditor@example.com", "password": "pass123"})
    token = login_resp.json()["access_token"]
    response = client.get("/audits/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json() == []
