"""
Integration tests for SecureTalkroom application.
Tests the complete flow from user registration to real-time messaging.
"""
import pytest
from fastapi.testclient import TestClient


class TestTalkroomIntegration:
    """Integration tests for the complete talkroom flow."""
    
    def test_complete_user_journey(self, client: TestClient):
        """Test complete user journey from registration to messaging."""
        
        # 1. Register two users
        user1_data = {
            "username": "alice",
            "email": "alice@example.com",
            "full_name": "Alice Smith",
            "password": "password123"
        }
        user2_data = {
            "username": "bob",
            "email": "bob@example.com", 
            "full_name": "Bob Johnson",
            "password": "password456"
        }
        
        # Register users
        response = client.post("/api/v1/auth/register", json=user1_data)
        assert response.status_code == 201
        user1_id = response.json()["id"]
        
        response = client.post("/api/v1/auth/register", json=user2_data)
        assert response.status_code == 201
        user2_id = response.json()["id"]
        
        # 2. Login both users
        login1_data = {"email": user1_data["email"], "password": user1_data["password"]}
        response = client.post("/api/v1/auth/login", json=login1_data)
        assert response.status_code == 200
        user1_tokens = response.json()
        auth_headers_1 = {"Authorization": f"Bearer {user1_tokens['access_token']}"}
        
        login2_data = {"email": user2_data["email"], "password": user2_data["password"]}
        response = client.post("/api/v1/auth/login", json=login2_data)
        assert response.status_code == 200
        user2_tokens = response.json()
        auth_headers_2 = {"Authorization": f"Bearer {user2_tokens['access_token']}"}
        
        # 3. Create a talkroom between users
        response = client.post(
            "/api/v1/talkroom/",
            headers=auth_headers_1,
            params={"other_user_id": user2_id}
        )
        assert response.status_code == 201
        talkroom = response.json()
        talkroom_id = talkroom["id"]
        
        # 4. Send messages between users
        message1_data = {
            "content": "Hello Bob! How are you?",
            "message_type": "text"
        }
        response = client.post(
            f"/api/v1/talkroom/{talkroom_id}/messages",
            headers=auth_headers_1,
            json=message1_data
        )
        assert response.status_code == 201
        message1 = response.json()
        assert message1["content"] == message1_data["content"]
        assert message1["sender_id"] == user1_id
        
        message2_data = {
            "content": "Hi Alice! I'm doing great, thanks!",
            "message_type": "text"
        }
        response = client.post(
            f"/api/v1/talkroom/{talkroom_id}/messages",
            headers=auth_headers_2,
            json=message2_data
        )
        assert response.status_code == 201
        message2 = response.json()
        assert message2["content"] == message2_data["content"]
        assert message2["sender_id"] == user2_id
        
        # 5. Get talkroom messages
        response = client.get(
            f"/api/v1/talkroom/{talkroom_id}/messages",
            headers=auth_headers_1
        )
        assert response.status_code == 200
        messages = response.json()
        assert len(messages) == 2
        assert messages[0]["content"] == message1_data["content"]
        assert messages[1]["content"] == message2_data["content"]
        
        # 6. Get user's talkrooms
        response = client.get("/api/v1/talkroom/my-talkrooms", headers=auth_headers_1)
        assert response.status_code == 200
        talkrooms = response.json()
        assert len(talkrooms) == 1
        assert talkrooms[0]["id"] == talkroom_id
        
        # 7. Update user profile
        update_data = {"full_name": "Alice Cooper"}
        response = client.put("/api/v1/users/me", headers=auth_headers_1, json=update_data)
        assert response.status_code == 200
        updated_user = response.json()
        assert updated_user["full_name"] == "Alice Cooper"
        
        # 8. Change password
        password_data = {
            "current_password": "password123",
            "new_password": "newpassword123"
        }
        response = client.put("/api/v1/auth/change-password", json=password_data, headers=auth_headers_1)
        assert response.status_code == 200
        
        # 9. Logout
        response = client.post("/api/v1/auth/logout", headers=auth_headers_1)
        assert response.status_code == 200
        
        # 10. Try to access protected endpoint after logout (should fail)
        response = client.get("/api/v1/users/me", headers=auth_headers_1)
        assert response.status_code == 401
    
    def test_message_pagination(self, client: TestClient):
        """Test message pagination in talkrooms."""
        # Create users and talkroom
        user1_data = {"username": "user1", "email": "user1@test.com", "full_name": "User One", "password": "pass123"}
        user2_data = {"username": "user2", "email": "user2@test.com", "full_name": "User Two", "password": "pass456"}
        
        client.post("/api/v1/auth/register", json=user1_data)
        client.post("/api/v1/auth/register", json=user2_data)
        
        # Login users
        login1 = client.post("/api/v1/auth/login", json={"email": user1_data["email"], "password": user1_data["password"]})
        login2 = client.post("/api/v1/auth/login", json={"email": user2_data["email"], "password": user2_data["password"]})
        
        auth1 = {"Authorization": f"Bearer {login1.json()['access_token']}"}
        auth2 = {"Authorization": f"Bearer {login2.json()['access_token']}"}
        
        # Get user2 ID
        user2_profile = client.get("/api/v1/users/me", headers=auth2)
        user2_id = user2_profile.json()["id"]
        
        # Create talkroom
        talkroom_response = client.post("/api/v1/talkroom/", headers=auth1, params={"other_user_id": user2_id})
        talkroom_id = talkroom_response.json()["id"]
        
        # Send multiple messages
        for i in range(25):
            message_data = {"content": f"Message {i+1}", "message_type": "text"}
            client.post(f"/api/v1/talkroom/{talkroom_id}/messages", headers=auth1, json=message_data)
        
        # Test pagination
        response = client.get(f"/api/v1/talkroom/{talkroom_id}/messages", headers=auth1, params={"limit": 10})
        assert response.status_code == 200
        messages = response.json()
        assert len(messages) == 10
        
        # Test offset
        response = client.get(f"/api/v1/talkroom/{talkroom_id}/messages", headers=auth1, params={"limit": 10, "offset": 10})
        assert response.status_code == 200
        messages = response.json()
        assert len(messages) == 10
    
    def test_talkroom_permissions(self, client: TestClient):
        """Test talkroom access permissions."""
        # Create 3 users
        users_data = [
            {"username": "user1", "email": "user1@test.com", "full_name": "User One", "password": "pass123"},
            {"username": "user2", "email": "user2@test.com", "full_name": "User Two", "password": "pass456"},
            {"username": "user3", "email": "user3@test.com", "full_name": "User Three", "password": "pass789"}
        ]
        
        tokens = []
        for user_data in users_data:
            client.post("/api/v1/auth/register", json=user_data)
            login_response = client.post("/api/v1/auth/login", json={"email": user_data["email"], "password": user_data["password"]})
            tokens.append(login_response.json()["access_token"])
        
        headers = [{"Authorization": f"Bearer {token}"} for token in tokens]
        
        # Get user IDs
        user_ids = []
        for header in headers:
            profile = client.get("/api/v1/users/me", headers=header)
            user_ids.append(profile.json()["id"])
        
        # Create talkroom between user 1 and user 2
        talkroom_response = client.post("/api/v1/talkroom/", headers=headers[0], params={"other_user_id": user_ids[1]})
        talkroom_id = talkroom_response.json()["id"]
        
        # User 1 and 2 should be able to send messages
        message_data = {"content": "Hello from user 1", "message_type": "text"}
        response = client.post(f"/api/v1/talkroom/{talkroom_id}/messages", headers=headers[0], json=message_data)
        assert response.status_code == 201
        
        message_data = {"content": "Hello from user 2", "message_type": "text"}
        response = client.post(f"/api/v1/talkroom/{talkroom_id}/messages", headers=headers[1], json=message_data)
        assert response.status_code == 201
        
        # User 3 should NOT be able to send messages (not in talkroom)
        message_data = {"content": "Hello from user 3", "message_type": "text"}
        response = client.post(f"/api/v1/talkroom/{talkroom_id}/messages", headers=headers[2], json=message_data)
        assert response.status_code == 403
        
        # User 3 should NOT be able to read messages
        response = client.get(f"/api/v1/talkroom/{talkroom_id}/messages", headers=headers[2])
        assert response.status_code == 403
    
    def test_error_handling(self, client: TestClient):
        """Test error handling across the application."""
        # Test invalid registration data
        invalid_user_data = {
            "username": "",  # Empty username
            "email": "invalid-email",  # Invalid email
            "full_name": "Test User",
            "password": "123"  # Too short password
        }
        response = client.post("/api/v1/auth/register", json=invalid_user_data)
        assert response.status_code == 422
        
        # Test accessing protected endpoint without token
        response = client.get("/api/v1/users/me")
        assert response.status_code == 401
        
        # Test invalid token
        invalid_headers = {"Authorization": "Bearer invalid-token"}
        response = client.get("/api/v1/users/me", headers=invalid_headers)
        assert response.status_code == 401
        
        # Test accessing non-existent talkroom
        valid_user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "full_name": "Test User",
            "password": "password123"
        }
        client.post("/api/v1/auth/register", json=valid_user_data)
        login_response = client.post("/api/v1/auth/login", json={"email": valid_user_data["email"], "password": valid_user_data["password"]})
        headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}
        
        response = client.get("/api/v1/talkroom/999999/messages", headers=headers)
        assert response.status_code == 404
    
    def test_health_and_status_endpoints(self, client: TestClient):
        """Test health and status endpoints."""
        # Test health endpoint
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "app_name" in data
        assert "version" in data
        
        # Test root endpoint
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data 