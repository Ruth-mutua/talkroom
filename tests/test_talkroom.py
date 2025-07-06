"""
Talkroom functionality tests.
"""
import pytest
from fastapi.testclient import TestClient


class TestTalkroom:
    """Test talkroom endpoints."""
    
    def test_create_talkroom(self, client: TestClient, auth_headers: dict, authenticated_user_2: dict):
        """Test creating a new talkroom."""
        # Get user 2's ID
        user2_response = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {authenticated_user_2['access_token']}"})
        user2_id = user2_response.json()["id"]
        
        # Create talkroom
        response = client.post("/api/v1/talkroom/", headers=auth_headers, params={"other_user_id": user2_id})
        
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert "created_at" in data
        assert "participants" in data
        assert len(data["participants"]) == 2
    
    def test_create_talkroom_with_self(self, client: TestClient, auth_headers: dict):
        """Test creating talkroom with yourself (should fail)."""
        # Get current user's ID
        user_response = client.get("/api/v1/users/me", headers=auth_headers)
        user_id = user_response.json()["id"]
        
        # Try to create talkroom with self
        response = client.post("/api/v1/talkroom/", headers=auth_headers, params={"other_user_id": user_id})
        
        assert response.status_code == 400
        assert "cannot create talkroom with yourself" in response.json()["detail"].lower()
    
    def test_create_duplicate_talkroom(self, client: TestClient, auth_headers: dict, authenticated_user_2: dict):
        """Test creating duplicate talkroom (should return existing one)."""
        # Get user 2's ID
        user2_response = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {authenticated_user_2['access_token']}"})
        user2_id = user2_response.json()["id"]
        
        # Create first talkroom
        response1 = client.post("/api/v1/talkroom/", headers=auth_headers, params={"other_user_id": user2_id})
        assert response1.status_code == 201
        talkroom1_id = response1.json()["id"]
        
        # Try to create duplicate talkroom
        response2 = client.post("/api/v1/talkroom/", headers=auth_headers, params={"other_user_id": user2_id})
        assert response2.status_code == 200  # Should return existing one
        talkroom2_id = response2.json()["id"]
        
        assert talkroom1_id == talkroom2_id
    
    def test_get_my_talkrooms(self, client: TestClient, auth_headers: dict, test_talkroom: dict):
        """Test getting user's talkrooms."""
        response = client.get("/api/v1/talkroom/my-talkrooms", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        # Check if our test talkroom is in the list
        talkroom_ids = [tr["id"] for tr in data]
        assert test_talkroom["id"] in talkroom_ids
    
    def test_get_talkroom_by_id(self, client: TestClient, auth_headers: dict, test_talkroom: dict):
        """Test getting talkroom by ID."""
        talkroom_id = test_talkroom["id"]
        
        response = client.get(f"/api/v1/talkroom/{talkroom_id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == talkroom_id
        assert "participants" in data
        assert "created_at" in data
    
    def test_get_nonexistent_talkroom(self, client: TestClient, auth_headers: dict):
        """Test getting non-existent talkroom."""
        response = client.get("/api/v1/talkroom/999999", headers=auth_headers)
        
        assert response.status_code == 404
        assert "Talkroom not found" in response.json()["detail"]
    
    def test_send_message(self, client: TestClient, auth_headers: dict, test_talkroom: dict):
        """Test sending a message to talkroom."""
        talkroom_id = test_talkroom["id"]
        message_data = {
            "content": "Hello, this is a test message!",
            "message_type": "text"
        }
        
        response = client.post(f"/api/v1/talkroom/{talkroom_id}/messages", headers=auth_headers, json=message_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["content"] == message_data["content"]
        assert data["message_type"] == message_data["message_type"]
        assert "id" in data
        assert "created_at" in data
        assert "sender_id" in data
    
    def test_send_empty_message(self, client: TestClient, auth_headers: dict, test_talkroom: dict):
        """Test sending empty message (should fail)."""
        talkroom_id = test_talkroom["id"]
        message_data = {
            "content": "",
            "message_type": "text"
        }
        
        response = client.post(f"/api/v1/talkroom/{talkroom_id}/messages", headers=auth_headers, json=message_data)
        
        assert response.status_code == 422
    
    def test_get_talkroom_messages(self, client: TestClient, auth_headers: dict, test_talkroom: dict, test_message: dict):
        """Test getting messages from talkroom."""
        talkroom_id = test_talkroom["id"]
        
        response = client.get(f"/api/v1/talkroom/{talkroom_id}/messages", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        # Check if our test message is in the list
        message_ids = [msg["id"] for msg in data]
        assert test_message["id"] in message_ids
    
    def test_get_messages_with_pagination(self, client: TestClient, auth_headers: dict, test_talkroom: dict):
        """Test getting messages with pagination."""
        talkroom_id = test_talkroom["id"]
        
        # Send multiple messages
        for i in range(5):
            message_data = {
                "content": f"Test message {i+1}",
                "message_type": "text"
            }
            client.post(f"/api/v1/talkroom/{talkroom_id}/messages", headers=auth_headers, json=message_data)
        
        # Test pagination
        response = client.get(f"/api/v1/talkroom/{talkroom_id}/messages", headers=auth_headers, params={"limit": 3})
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        
        # Test offset
        response = client.get(f"/api/v1/talkroom/{talkroom_id}/messages", headers=auth_headers, params={"limit": 3, "offset": 3})
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
    
    def test_unauthorized_access_to_talkroom(self, client: TestClient, auth_headers: dict, auth_headers_2: dict):
        """Test unauthorized access to talkroom."""
        # Create talkroom with user 1
        user2_response = client.get("/api/v1/users/me", headers=auth_headers_2)
        user2_id = user2_response.json()["id"]
        
        response = client.post("/api/v1/talkroom/", headers=auth_headers, params={"other_user_id": user2_id})
        talkroom_id = response.json()["id"]
        
        # Create a third user who shouldn't have access
        user3_data = {
            "username": "unauthorizeduser",
            "email": "unauthorized@example.com",
            "full_name": "Unauthorized User",
            "password": "password123"
        }
        client.post("/api/v1/auth/register", json=user3_data)
        
        login_response = client.post("/api/v1/auth/login", json={"email": user3_data["email"], "password": user3_data["password"]})
        auth_headers_3 = {"Authorization": f"Bearer {login_response.json()['access_token']}"}
        
        # Try to access talkroom (should fail)
        response = client.get(f"/api/v1/talkroom/{talkroom_id}", headers=auth_headers_3)
        assert response.status_code == 403
        
        # Try to send message (should fail)
        message_data = {"content": "Unauthorized message", "message_type": "text"}
        response = client.post(f"/api/v1/talkroom/{talkroom_id}/messages", headers=auth_headers_3, json=message_data)
        assert response.status_code == 403
    
    def test_message_timestamps(self, client: TestClient, auth_headers: dict, test_talkroom: dict):
        """Test message timestamps are properly set."""
        talkroom_id = test_talkroom["id"]
        message_data = {
            "content": "Test message with timestamp",
            "message_type": "text"
        }
        
        response = client.post(f"/api/v1/talkroom/{talkroom_id}/messages", headers=auth_headers, json=message_data)
        
        assert response.status_code == 201
        data = response.json()
        assert "created_at" in data
        assert "updated_at" in data
        
        # Check timestamp format (ISO 8601)
        import datetime
        try:
            datetime.datetime.fromisoformat(data["created_at"].replace('Z', '+00:00'))
            datetime.datetime.fromisoformat(data["updated_at"].replace('Z', '+00:00'))
        except ValueError:
            pytest.fail("Invalid timestamp format")
    
    def test_different_message_types(self, client: TestClient, auth_headers: dict, test_talkroom: dict):
        """Test sending different types of messages."""
        talkroom_id = test_talkroom["id"]
        
        message_types = [
            {"content": "Text message", "message_type": "text"},
            {"content": "System message", "message_type": "system"},
            {"content": "Image message", "message_type": "image"},
            {"content": "File message", "message_type": "file"}
        ]
        
        for message_data in message_types:
            response = client.post(f"/api/v1/talkroom/{talkroom_id}/messages", headers=auth_headers, json=message_data)
            
            assert response.status_code == 201
            data = response.json()
            assert data["message_type"] == message_data["message_type"]
            assert data["content"] == message_data["content"] 