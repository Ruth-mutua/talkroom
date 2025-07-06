"""
User management tests.
"""
import pytest
from fastapi.testclient import TestClient


class TestUsers:
    """Test user management endpoints."""
    
    def test_get_current_user(self, client: TestClient, auth_headers: dict):
        """Test getting current user profile."""
        response = client.get("/api/v1/users/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "email" in data
        assert "username" in data
        assert "full_name" in data
        assert "hashed_password" not in data
        assert "created_at" in data
        assert "updated_at" in data
    
    def test_update_user_profile(self, client: TestClient, auth_headers: dict):
        """Test updating user profile."""
        update_data = {
            "full_name": "Updated Name",
            "bio": "Updated bio information"
        }
        
        response = client.put("/api/v1/users/me", headers=auth_headers, json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Name"
        assert data["bio"] == "Updated bio information"
    
    def test_update_user_email(self, client: TestClient, auth_headers: dict):
        """Test updating user email."""
        update_data = {
            "email": "newemail@example.com"
        }
        
        response = client.put("/api/v1/users/me", headers=auth_headers, json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "newemail@example.com"
    
    def test_get_user_by_id(self, client: TestClient, auth_headers: dict, authenticated_user_2: dict):
        """Test getting user by ID."""
        # Get user 2's profile to get their ID
        user2_response = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {authenticated_user_2['access_token']}"})
        user2_id = user2_response.json()["id"]
        
        # Get user 2's profile via ID
        response = client.get(f"/api/v1/users/{user2_id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user2_id
        assert "email" in data
        assert "username" in data
        assert "hashed_password" not in data
    
    def test_get_nonexistent_user(self, client: TestClient, auth_headers: dict):
        """Test getting non-existent user."""
        response = client.get("/api/v1/users/999999", headers=auth_headers)
        
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]
    
    def test_search_users(self, client: TestClient, auth_headers: dict):
        """Test searching users."""
        # Search by username
        response = client.get("/api/v1/users/search", headers=auth_headers, params={"query": "testuser"})
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should find at least one user
        assert len(data) >= 1
    
    def test_get_user_talkrooms(self, client: TestClient, auth_headers: dict, test_talkroom: dict):
        """Test getting user's talkrooms."""
        response = client.get("/api/v1/users/me/talkrooms", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        # Check if our test talkroom is in the list
        talkroom_ids = [tr["id"] for tr in data]
        assert test_talkroom["id"] in talkroom_ids
    
    def test_update_user_invalid_data(self, client: TestClient, auth_headers: dict):
        """Test updating user with invalid data."""
        update_data = {
            "email": "invalid-email-format"
        }
        
        response = client.put("/api/v1/users/me", headers=auth_headers, json=update_data)
        
        assert response.status_code == 422
    
    def test_get_users_without_auth(self, client: TestClient):
        """Test accessing user endpoints without authentication."""
        response = client.get("/api/v1/users/me")
        
        assert response.status_code == 401
    
    def test_update_user_partial(self, client: TestClient, auth_headers: dict):
        """Test partial user update."""
        # Only update one field
        update_data = {
            "full_name": "Only Name Changed"
        }
        
        response = client.put("/api/v1/users/me", headers=auth_headers, json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Only Name Changed"
        # Email should remain unchanged
        assert "email" in data 