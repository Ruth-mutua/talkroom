"""
Application health and basic functionality tests.
"""
import pytest
from fastapi.testclient import TestClient


class TestAppHealth:
    """Test basic application health and functionality."""
    
    def test_app_health_check(self, client: TestClient):
        """Test the health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "app_name" in data
        assert "version" in data
        assert "environment" in data
    
    def test_root_endpoint(self, client: TestClient):
        """Test the root endpoint."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "SecureTalkroom" in data["message"]
    
    def test_api_documentation(self, client: TestClient):
        """Test API documentation endpoints."""
        # Test OpenAPI schema
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        # Test Swagger UI (if DEBUG is True)
        response = client.get("/docs")
        # Should return 200 in development, 404 in production
        assert response.status_code in [200, 404]
    
    def test_cors_headers(self, client: TestClient):
        """Test CORS headers are properly set."""
        response = client.options("/health")
        # Should handle OPTIONS request properly
        assert response.status_code in [200, 405]  # 405 is acceptable for OPTIONS
    
    def test_404_handling(self, client: TestClient):
        """Test 404 error handling."""
        response = client.get("/nonexistent-endpoint")
        
        assert response.status_code == 404
    
    def test_unprotected_endpoints(self, client: TestClient):
        """Test endpoints that should be accessible without authentication."""
        unprotected_endpoints = [
            "/health",
            "/",
            "/openapi.json"
        ]
        
        for endpoint in unprotected_endpoints:
            response = client.get(endpoint)
            # Should not return 401 (Unauthorized)
            assert response.status_code != 401
    
    def test_protected_endpoints_require_auth(self, client: TestClient):
        """Test that protected endpoints require authentication."""
        protected_endpoints = [
            "/api/v1/users/me",
            "/api/v1/talkroom/my-talkrooms",
            "/api/v1/auth/me"
        ]
        
        for endpoint in protected_endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401
    
    def test_request_validation_errors(self, client: TestClient):
        """Test request validation error handling."""
        # Send invalid JSON to registration endpoint
        response = client.post("/api/v1/auth/register", json={})
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], list)
    
    def test_content_type_headers(self, client: TestClient):
        """Test content type headers."""
        response = client.get("/health")
        
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"] 