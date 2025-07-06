"""
Authentication tests.
"""
import pytest
from fastapi.testclient import TestClient


class TestAuthentication:
    """Test authentication endpoints."""
    
    def test_register_user(self, client: TestClient, test_user_data: dict):
        """Test user registration."""
        response = client.post("/api/v1/auth/register", json=test_user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert data["username"] == test_user_data["username"]
        assert data["full_name"] == test_user_data["full_name"]
        assert "id" in data
        assert "hashed_password" not in data
    
    def test_register_duplicate_email(self, client: TestClient, test_user_data: dict):
        """Test registration with duplicate email."""
        # Register first user
        response = client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == 201
        
        # Try to register with same email
        duplicate_data = test_user_data.copy()
        duplicate_data["username"] = "different_username"
        response = client.post("/api/v1/auth/register", json=duplicate_data)
        
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]
    
    def test_register_duplicate_username(self, client: TestClient, test_user_data: dict):
        """Test registration with duplicate username."""
        # Register first user
        response = client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == 201
        
        # Try to register with same username
        duplicate_data = test_user_data.copy()
        duplicate_data["email"] = "different@example.com"
        response = client.post("/api/v1/auth/register", json=duplicate_data)
        
        assert response.status_code == 409
        assert "already taken" in response.json()["detail"]
    
    def test_login_valid_credentials(self, client: TestClient, test_user_data: dict):
        """Test login with valid credentials."""
        # Register user first
        client.post("/api/v1/auth/register", json=test_user_data)
        
        # Login
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_invalid_email(self, client: TestClient):
        """Test login with invalid email."""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "somepassword"
        }
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]
    
    def test_login_invalid_password(self, client: TestClient, test_user_data: dict):
        """Test login with invalid password."""
        # Register user first
        client.post("/api/v1/auth/register", json=test_user_data)
        
        # Login with wrong password
        login_data = {
            "email": test_user_data["email"],
            "password": "wrongpassword"
        }
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]
    
    def test_get_current_user(self, client: TestClient, auth_headers: dict):
        """Test getting current user profile."""
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "email" in data
        assert "username" in data
        assert "hashed_password" not in data
    
    def test_get_current_user_unauthorized(self, client: TestClient):
        """Test getting current user without token."""
        response = client.get("/api/v1/auth/me")
        
        assert response.status_code == 401
    
    def test_refresh_token(self, client: TestClient, test_user_data: dict):
        """Test token refresh."""
        # Register and login
        client.post("/api/v1/auth/register", json=test_user_data)
        
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        response = client.post("/api/v1/auth/login", json=login_data)
        refresh_token = response.json()["refresh_token"]
        
        # Refresh token
        refresh_data = {"refresh_token": refresh_token}
        response = client.post("/api/v1/auth/refresh", json=refresh_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
    
    def test_refresh_invalid_token(self, client: TestClient):
        """Test refresh with invalid token."""
        refresh_data = {"refresh_token": "invalid_token"}
        response = client.post("/api/v1/auth/refresh", json=refresh_data)
        
        assert response.status_code == 401
    
    def test_change_password(self, client: TestClient, auth_headers: dict):
        """Test password change."""
        password_data = {
            "current_password": "testpassword123",
            "new_password": "newpassword123"
        }
        response = client.put("/api/v1/auth/change-password", json=password_data, headers=auth_headers)
        
        assert response.status_code == 200
        assert "Password changed successfully" in response.json()["message"]
    
    def test_change_password_wrong_current(self, client: TestClient, auth_headers: dict):
        """Test password change with wrong current password."""
        password_data = {
            "current_password": "wrongpassword",
            "new_password": "newpassword123"
        }
        response = client.put("/api/v1/auth/change-password", json=password_data, headers=auth_headers)
        
        assert response.status_code == 401
        assert "Current password is incorrect" in response.json()["detail"]
    
    def test_logout(self, client: TestClient, auth_headers: dict):
        """Test logout."""
        response = client.post("/api/v1/auth/logout", headers=auth_headers)
        
        assert response.status_code == 200
        assert "Logged out successfully" in response.json()["message"] 