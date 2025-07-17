"""
Authentication API tests
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from app.main import app
from app.core.auth import hash_password

client = TestClient(app)

@pytest.fixture
def setup_test_user(monkeypatch):
    """Set up a test user in the database"""
    async def mock_fetch_one(query):
        return None
        
    async def mock_execute(query):
        return 1
        
    async def mock_fetch_user(query):
        return {
            "id": 1,
            "username": "testuser",
            "email": "test@example.com",
            "hashed_password": hash_password("password123"),
            "is_active": True,
            "created_at": datetime.utcnow(),
            "last_login": None
        }
        
    # Mock database calls
    monkeypatch.setattr("app.db.database.fetch_one", mock_fetch_one)
    monkeypatch.setattr("app.db.database.execute", mock_execute)
    
    # For login specifically
    monkeypatch.setattr("app.api.auth.database.fetch_one", mock_fetch_user)
    monkeypatch.setattr("app.api.auth.database.execute", mock_execute)


def test_register_user(setup_test_user):
    """Test user registration endpoint"""
    response = client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert "id" in data


def test_login_user(setup_test_user):
    """Test user login endpoint"""
    response = client.post(
        "/api/auth/login",
        json={
            "username": "testuser",
            "password": "password123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "testuser"


def test_current_user(setup_test_user):
    """Test getting current user info"""
    # First login to get a token
    login_response = client.post(
        "/api/auth/login",
        json={
            "username": "testuser",
            "password": "password123"
        }
    )
    token = login_response.json()["access_token"]
    
    # Then use the token to get user info
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
