"""
Test configuration and fixtures for SecureTalkroom application.
"""
import asyncio
import os
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.database import Base, get_db
from app.main import app

# Test database URL
TEST_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/test_secure_talkroom"

# Create test engine
test_engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def setup_database():
    """Set up the test database."""
    # Create all tables
    Base.metadata.create_all(bind=test_engine)
    yield
    # Drop all tables
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session(setup_database):
    """Create a database session for testing."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    """Create a test client with database session override."""
    
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
def mock_redis():
    """Mock Redis for testing."""
    return AsyncMock()


@pytest.fixture
def test_user_data():
    """Test user data."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "testpassword123"
    }


@pytest.fixture
def test_user_data_2():
    """Second test user data."""
    return {
        "username": "testuser2",
        "email": "test2@example.com",
        "full_name": "Test User 2",
        "password": "testpassword456"
    }


@pytest.fixture
def test_talkroom_data():
    """Test talkroom data."""
    return {
        "name": "Test Talkroom",
        "description": "A test talkroom"
    }


@pytest.fixture
def test_message_data():
    """Test message data."""
    return {
        "content": "Hello, this is a test message!",
        "message_type": "text"
    }


@pytest.fixture
def authenticated_user(client, test_user_data):
    """Create an authenticated user and return tokens."""
    # Register user
    response = client.post("/api/v1/auth/register", json=test_user_data)
    assert response.status_code == 201
    
    # Login user
    login_data = {
        "username": test_user_data["username"],
        "password": test_user_data["password"]
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200
    
    return response.json()


@pytest.fixture
def authenticated_user_2(client, test_user_data_2):
    """Create a second authenticated user and return tokens."""
    # Register user
    response = client.post("/api/v1/auth/register", json=test_user_data_2)
    assert response.status_code == 201
    
    # Login user
    login_data = {
        "username": test_user_data_2["username"],
        "password": test_user_data_2["password"]
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200
    
    return response.json()


@pytest.fixture
def auth_headers(authenticated_user):
    """Get authentication headers for requests."""
    return {"Authorization": f"Bearer {authenticated_user['access_token']}"}


@pytest.fixture
def auth_headers_2(authenticated_user_2):
    """Get authentication headers for second user."""
    return {"Authorization": f"Bearer {authenticated_user_2['access_token']}"}


@pytest.fixture
def test_talkroom(client, authenticated_user, authenticated_user_2, auth_headers):
    """Create a test talkroom between two users."""
    # Get the second user's ID
    user_2_response = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {authenticated_user_2['access_token']}"})
    user_2_id = user_2_response.json()["id"]
    
    # Create talkroom
    response = client.post(
        "/api/v1/talkroom/",
        headers=auth_headers,
        params={"other_user_id": user_2_id}
    )
    assert response.status_code == 201
    
    return response.json()


@pytest.fixture
def test_message(client, test_talkroom, auth_headers, test_message_data):
    """Create a test message in a talkroom."""
    message_data = {
        "talkroom_id": test_talkroom["id"],
        **test_message_data
    }
    
    response = client.post(
        f"/api/v1/talkroom/{test_talkroom['id']}/messages",
        headers=auth_headers,
        json=message_data
    )
    assert response.status_code == 201
    
    return response.json()


# Environment variable fixtures
@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    os.environ["ENVIRONMENT"] = "testing"
    os.environ["DEBUG"] = "True"
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
    os.environ["REDIS_URL"] = "redis://localhost:6379/1"
    yield
    # Clean up is handled by pytest


# Async fixtures for async tests
@pytest_asyncio.fixture
async def async_client():
    """Create an async test client."""
    from httpx import AsyncClient
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def async_db_session():
    """Create an async database session for testing."""
    async_engine = create_async_engine(TEST_DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"))
    async_session = sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session 