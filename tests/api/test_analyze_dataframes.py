"""
Test Suite for DataFrame Analysis API Endpoints

These tests verify the functionality of the API endpoints related to DataFrame analysis:
- /api/projects/{project_id}/analyze
- /api/analyze with data analysis intent
"""

import pytest
import pandas as pd
import numpy as np
import json
import sys
import os
import httpx
from typing import Dict, Any, List, Optional

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# Import pytest fixtures
from tests.conftest import test_client, auth_token, test_user, base_url


@pytest.fixture
def sample_dataframe() -> pd.DataFrame:
    """Create a sample DataFrame with various data types for testing"""
    # Create sample data
    data = {
        'order_id': [f'ORD-{i:04d}' for i in range(1, 21)],
        'customer_name': [f'Customer {i}' for i in range(1, 21)],
        'order_date': pd.date_range(start='2024-01-01', periods=20).astype(str),
        'amount': np.random.uniform(50, 500, 20).round(2).tolist(),
        'item_count': np.random.randint(1, 10, 20).tolist(),
        'status': np.random.choice(['Pending', 'Shipped', 'Delivered', 'Cancelled'], 20).tolist(),
        'payment_method': np.random.choice(['Credit Card', 'PayPal', 'Bank Transfer'], 20).tolist(),
    }
    
    return pd.DataFrame(data)


@pytest.fixture
def auth_headers(auth_token):
    """Return headers with authentication token"""
    if not auth_token:
        pytest.skip("No authentication token available")
    return {"Authorization": f"Bearer {auth_token}"}

@pytest.fixture
def create_test_project(test_client, auth_headers):
    """Helper function to create a test project"""
    project_data = {
        "name": "Analysis Test Project",
        "persona": "Data Analyst",
        "context": "Testing the DataFrame analysis functionality",
        "industry": "E-Commerce"
    }
    
    response = test_client.post("/api/projects", json=project_data, headers=auth_headers)
    assert response.status_code == 200, f"Failed to create project: {response.text}"
    return response.json()

@pytest.fixture
def project_with_data(test_client, auth_headers, sample_dataframe, create_test_project) -> Dict[str, Any]:
    """Create a test project and associate sample data with it"""
    # We already have the test project from the fixture
    project = create_test_project
    
    # Mock the association of data with the project (normally done through Salla integration)
    # This is a simplified approach for testing - in a real scenario, we'd use the Salla endpoints
    df_dict = sample_dataframe.to_dict(orient="records")
    
    # Send a data analysis request to simulate having data in the project
    analyze_data = {
        "messages": [
            {"role": "user", "content": "Analyze my sales data"}
        ],
        "project_id": project["id"],
        "dataframe": df_dict,
        "persona": "Data Analyst",
        "industry": "E-Commerce",
        "business_context": "Testing DataFrame analysis"
    }
    
    response = test_client.post("/api/analyze", json=analyze_data, headers=auth_headers)
    assert response.status_code == 200, f"Failed to simulate data analysis: {response.text}"
    
    return project


def test_analyze_project_endpoint(test_client, auth_headers, project_with_data):
    """Test the /api/projects/{project_id}/analyze endpoint"""
    project_id = project_with_data["id"]
    
    # Call the analyze endpoint
    response = test_client.post(f"/api/projects/{project_id}/analyze", headers=auth_headers)
    
    # Assert response is successful
    assert response.status_code == 200, f"Failed to analyze project: {response.text}"
    
    # Verify response structure
    data = response.json()
    assert "message" in data
    assert "project_id" in data
    assert data["project_id"] == project_id
    
    # Should include metadata summary
    assert "metadata_summary" in data
    assert "dataframe_count" in data["metadata_summary"]
    assert "total_rows" in data["metadata_summary"]
    assert "total_columns" in data["metadata_summary"]


def test_analyze_endpoint_with_data_analysis(test_client, auth_headers, project_with_data, sample_dataframe):
    """Test the /api/analyze endpoint with data analysis intent"""
    project_id = project_with_data["id"]
    df_dict = sample_dataframe.to_dict(orient="records")
    
    # Create a request that should trigger data analysis
    analyze_data = {
        "messages": [
            {"role": "user", "content": "What is the average order amount?"}
        ],
        "project_id": project_id,
        "dataframe": df_dict,
        "persona": "Data Analyst",
        "industry": "E-Commerce",
        "business_context": "Testing DataFrame analysis"
    }
    
    response = test_client.post("/api/analyze", json=analyze_data, headers=auth_headers)
    
    # Assert response is successful
    assert response.status_code == 200, f"Failed to analyze data: {response.text}"
    
    # The response should be data analysis type
    data = response.json()
    assert "type" in data
    assert data["type"] == "data_analysis"
    assert "pandas_result" in data
    assert "narrative" in data


def test_get_project_context_includes_metadata(test_client, auth_headers, project_with_data):
    """Test that the project context endpoint returns analysis metadata"""
    project_id = project_with_data["id"]
    
    # First trigger analysis to ensure metadata is generated
    test_client.post(f"/api/projects/{project_id}/analyze", headers=auth_headers)
    
    # Then get the project context
    response = test_client.get(f"/api/projects/{project_id}/context", headers=auth_headers)
    
    # Assert response is successful
    assert response.status_code == 200, f"Failed to get project context: {response.text}"
    
    # Check for metadata in project
    data = response.json()
    assert "project" in data
    project = data["project"]
    
    # The data_analysis field might not exist immediately as it's updated asynchronously
    # So this is a soft check - if it exists, verify its structure
    if "data_analysis" in project:
        assert "dataframes" in project["data_analysis"]
        assert isinstance(project["data_analysis"]["dataframes"], list)
        
        # If we have dataframes, check their structure
        if project["data_analysis"]["dataframes"]:
            df_meta = project["data_analysis"]["dataframes"][0]
            assert "columns" in df_meta
            assert "sample" in df_meta
            assert "total_rows" in df_meta
