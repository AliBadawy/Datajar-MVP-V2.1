import pytest
import uuid
import httpx
from jose import jwt
import os

class TestAuthentication:
    """Test suite for authentication endpoints."""
    
    def test_signup(self, test_client):
        """Test user signup functionality."""
        # Generate a unique email for this test
        unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        
        signup_data = {
            "email": unique_email,
            "password": "TestPassword123!",
            "name": "Test User"
        }
        
        response = test_client.post("/auth/signup", json=signup_data)
        
        assert response.status_code in (200, 201), f"Failed to sign up: {response.text}"
        data = response.json()
        
        # Check that response contains user data and token
        assert "user" in data, "Response does not contain user data"
        assert "token" in data, "Response does not contain authentication token"
        assert data["user"]["email"] == unique_email, "Email in response doesn't match request"
    
    def test_login_success(self, test_client, test_user):
        """Test successful login with valid credentials."""
        login_data = {
            "email": test_user["email"],
            "password": test_user["password"]
        }
        
        response = test_client.post("/auth/login", json=login_data)
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        
        # Check response structure
        assert "token" in data, "Response does not contain authentication token"
        assert "user" in data, "Response does not contain user data"
        
        # Verify token is valid JWT
        token = data["token"]
        jwt_secret = os.getenv("SUPABASE_JWT_SECRET", "your-jwt-secret")
        try:
            decoded = jwt.decode(token, jwt_secret, algorithms=["HS256"])
            assert "sub" in decoded, "JWT token doesn't contain subject claim"
            assert "email" in decoded, "JWT token doesn't contain email claim"
        except Exception as e:
            pytest.fail(f"Invalid JWT token: {str(e)}")
    
    def test_login_failure(self, test_client):
        """Test login failure with invalid credentials."""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "WrongPassword123!"
        }
        
        response = test_client.post("/auth/login", json=login_data)
        
        # Should fail with 401 Unauthorized
        assert response.status_code == 401, "Login with invalid credentials should fail"
    
    def test_token_validation(self, test_client, auth_token, auth_headers):
        """Test that protected endpoints require valid token."""
        # Try accessing a protected endpoint with a valid token
        with_token = test_client.get("/api/projects", headers=auth_headers)
        assert with_token.status_code in (200, 204), "Access with valid token failed"
        
        # Try accessing without a token
        without_token = test_client.get("/api/projects")
        assert without_token.status_code in (401, 403), "Access without token should be denied"
        
        # Try with an invalid token
        invalid_headers = {"Authorization": "Bearer invalid-token"}
        with_invalid_token = test_client.get("/api/projects", headers=invalid_headers)
        assert with_invalid_token.status_code in (401, 403), "Access with invalid token should be denied"
