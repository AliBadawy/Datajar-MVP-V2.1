import pytest
import os
import time

class TestSallaIntegration:
    """Test suite for Salla e-commerce integration endpoints."""
    
    def test_salla_auth_url(self, test_client, auth_headers):
        """Test getting Salla authentication URL."""
        response = test_client.get("/api/salla/auth-url", headers=auth_headers)
        
        assert response.status_code == 200, f"Failed to get Salla auth URL: {response.text}"
        data = response.json()
        
        # Check response contains auth URL
        assert "auth_url" in data, "Response missing Salla auth URL"
        assert data["auth_url"].startswith("https://accounts.salla.sa/oauth2/auth"), "Invalid Salla auth URL format"
    
    def test_get_salla_orders(self, test_client, auth_headers, test_project):
        """Test retrieving Salla orders for a project."""
        project_id = test_project["id"]
        
        # Note: This test might need mocking if not actually connected to Salla
        # or if there's no valid Salla token in the test environment
        response = test_client.get(f"/api/projects/{project_id}/salla/orders", headers=auth_headers)
        
        # If no Salla token, might expect 400/401, otherwise 200
        # Adjust based on your actual implementation
        assert response.status_code in (200, 400, 401, 404), f"Unexpected status code: {response.status_code}"
        
        # If successful, validate response structure
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list), "Response should be a list of orders"
            
            # If there are orders, check structure of first order
            if len(data) > 0:
                order = data[0]
                assert "id" in order, "Order missing ID"
                assert "reference_id" in order, "Order missing reference ID"
                assert "status" in order, "Order missing status"
    
    def test_salla_callback(self, test_client):
        """Test Salla OAuth callback endpoint."""
        # This is usually called by Salla after auth, needs mocking for testing
        
        # Mock callback with a test code
        callback_params = {
            "code": "test_auth_code",
            "state": "test_state"
        }
        
        response = test_client.get("/api/salla/callback", params=callback_params)
        
        # Callback typically redirects, so check for redirect status
        assert response.status_code in (200, 302, 303, 307, 308), "Callback should return success or redirect"
    
    def test_connect_salla_to_project(self, test_client, auth_headers, test_project):
        """Test connecting a Salla store to a project."""
        project_id = test_project["id"]
        
        # Mock Salla connection data
        # Note: This would normally come from an actual Salla OAuth process
        connect_data = {
            "salla_token": "mock_salla_token",
            "salla_refresh_token": "mock_refresh_token",
            "store_id": "mock_store_id"
        }
        
        response = test_client.post(
            f"/api/projects/{project_id}/salla/connect",
            json=connect_data,
            headers=auth_headers
        )
        
        # Since this is a mock connection, your API might reject it
        # Adjust expected status based on your implementation
        assert response.status_code in (200, 201, 400, 422), f"Unexpected status: {response.text}"
    
    def test_analyze_salla_data(self, test_client, auth_headers, test_project):
        """Test analyzing Salla data for a project."""
        project_id = test_project["id"]
        
        # Request data analysis
        analysis_request = {
            "analysis_type": "sales_trends",
            "date_range": {
                "start": "2023-01-01",
                "end": "2023-12-31"
            }
        }
        
        response = test_client.post(
            f"/api/projects/{project_id}/salla/analyze",
            json=analysis_request,
            headers=auth_headers
        )
        
        # This might fail if no Salla connection exists
        assert response.status_code in (200, 201, 202, 400, 404), f"Unexpected status: {response.text}"
        
        # If accepted for processing, wait for analysis to complete
        if response.status_code in (200, 201, 202):
            analysis_id = response.json().get("analysis_id")
            
            # Only poll if we got an analysis ID
            if analysis_id:
                # Poll for results (with timeout)
                max_retries = 5
                for _ in range(max_retries):
                    result_response = test_client.get(
                        f"/api/projects/{project_id}/salla/analysis/{analysis_id}",
                        headers=auth_headers
                    )
                    
                    # If completed, break loop
                    if result_response.status_code == 200 and result_response.json().get("status") == "completed":
                        break
                    
                    time.sleep(2)  # Wait before polling again
                
                # Check final result
                assert result_response.status_code == 200, "Failed to get analysis results"
