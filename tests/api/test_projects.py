import pytest
import uuid

class TestProjects:
    """Test suite for project management endpoints."""
    
    def test_get_projects(self, test_client, auth_headers):
        """Test retrieving all projects for the authenticated user."""
        response = test_client.get("/api/projects", headers=auth_headers)
        
        assert response.status_code == 200, f"Failed to get projects: {response.text}"
        data = response.json()
        
        # Check response is a list
        assert isinstance(data, list), "Response should be a list of projects"
    
    def test_create_project(self, test_client, auth_headers):
        """Test creating a new project."""
        # Generate unique project name
        unique_name = f"Test Project {uuid.uuid4().hex[:8]}"
        
        project_data = {
            "name": unique_name,
            "description": "A test project created via API tests",
            "tags": ["api-test", "automated"]
        }
        
        response = test_client.post("/api/projects", json=project_data, headers=auth_headers)
        
        assert response.status_code in (200, 201), f"Failed to create project: {response.text}"
        data = response.json()
        
        # Validate response fields
        assert "id" in data, "Response missing project ID"
        assert data["name"] == unique_name, "Project name in response doesn't match request"
        assert data["description"] == project_data["description"], "Project description in response doesn't match"
        
        # Store project ID for later tests
        project_id = data["id"]
        return project_id
    
    def test_get_project_details(self, test_client, auth_headers, test_project):
        """Test retrieving details for a specific project."""
        project_id = test_project["id"]
        
        response = test_client.get(f"/api/projects/{project_id}", headers=auth_headers)
        
        assert response.status_code == 200, f"Failed to get project details: {response.text}"
        data = response.json()
        
        # Validate response matches the test project
        assert data["id"] == project_id, "Project ID in response doesn't match"
        assert data["name"] == test_project["name"], "Project name in response doesn't match"
    
    def test_update_project(self, test_client, auth_headers, test_project):
        """Test updating an existing project."""
        project_id = test_project["id"]
        
        # Updated project data
        updated_data = {
            "name": f"{test_project['name']} (updated)",
            "description": f"{test_project['description']} - with updates",
            "tags": test_project.get("tags", []) + ["updated"]
        }
        
        response = test_client.put(f"/api/projects/{project_id}", json=updated_data, headers=auth_headers)
        
        assert response.status_code == 200, f"Failed to update project: {response.text}"
        data = response.json()
        
        # Validate updated fields
        assert data["id"] == project_id, "Project ID in response doesn't match"
        assert data["name"] == updated_data["name"], "Updated name not reflected in response"
        assert data["description"] == updated_data["description"], "Updated description not reflected in response"
    
    def test_delete_project(self, test_client, auth_headers):
        """Test deleting a project."""
        # First create a project specifically for deletion
        project_data = {
            "name": f"Delete Test Project {uuid.uuid4().hex[:6]}",
            "description": "This project will be deleted",
            "tags": ["temporary"]
        }
        
        create_response = test_client.post("/api/projects", json=project_data, headers=auth_headers)
        assert create_response.status_code in (200, 201), "Failed to create project for deletion test"
        
        project_id = create_response.json()["id"]
        
        # Now delete the project
        delete_response = test_client.delete(f"/api/projects/{project_id}", headers=auth_headers)
        
        assert delete_response.status_code in (200, 204), f"Failed to delete project: {delete_response.text}"
        
        # Verify project is deleted by trying to get it
        get_response = test_client.get(f"/api/projects/{project_id}", headers=auth_headers)
        assert get_response.status_code == 404, "Project should not be found after deletion"
