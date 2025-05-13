import os
import pytest
import httpx
from dotenv import load_dotenv
from jose import jwt

# Load test environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '.env.test'))

# Get base URL from environment or use default for Railway deployment
BASE_URL = os.getenv('API_BASE_URL', 'https://datajar-mvp-v21-production.up.railway.app')

@pytest.fixture(scope="session")
def base_url():
    """Return the base URL for API testing."""
    return BASE_URL

@pytest.fixture(scope="session")
def test_client():
    """Return a test client for making HTTP requests."""
    with httpx.Client(base_url=BASE_URL, timeout=30.0) as client:
        yield client

@pytest.fixture(scope="session")
def test_user():
    """Return test user credentials."""
    return {
        "email": os.getenv("TEST_USER_EMAIL", "test@example.com"),
        "password": os.getenv("TEST_USER_PASSWORD", "TestPassword123!"),
        "name": "Test User"
    }

@pytest.fixture(scope="session")
def auth_token(test_client, test_user):
    """Get an authentication token for API requests."""
    response = test_client.post(
        "/auth/login",
        json={
            "email": test_user["email"],
            "password": test_user["password"]
        }
    )
    
    if response.status_code == 200:
        return response.json().get("token")
    else:
        # If login fails, we might need to register first
        register_response = test_client.post(
            "/auth/signup",
            json={
                "email": test_user["email"],
                "password": test_user["password"],
                "name": test_user["name"]
            }
        )
        
        if register_response.status_code in (200, 201):
            # Try login again
            login_response = test_client.post(
                "/auth/login",
                json={
                    "email": test_user["email"],
                    "password": test_user["password"]
                }
            )
            return login_response.json().get("token")
    
    # If we get here, authentication failed
    pytest.fail("Failed to authenticate test user")

@pytest.fixture(scope="session")
def auth_headers(auth_token):
    """Return headers with authentication token."""
    return {"Authorization": f"Bearer {auth_token}"}

@pytest.fixture(scope="function")
def test_project(test_client, auth_headers):
    """Create a test project for testing."""
    # Create a test project
    project_data = {
        "name": "Test Project",
        "description": "Project created for automated testing",
        "tags": ["test", "automation"]
    }
    
    response = test_client.post("/api/projects", json=project_data, headers=auth_headers)
    
    if response.status_code in (200, 201):
        project = response.json()
        yield project
        
        # Cleanup (delete project) - optional depending on your needs
        # test_client.delete(f"/api/projects/{project['id']}", headers=auth_headers)
    else:
        pytest.fail(f"Failed to create test project: {response.text}")
