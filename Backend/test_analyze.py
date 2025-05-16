"""
Test script for the DataFrame analysis functionality.

This script tests the DataFrame analysis endpoints by:
1. Creating a sample project
2. Uploading sample data to it
3. Triggering the analysis endpoint
4. Verifying that the metadata is generated correctly
"""

import requests
import pandas as pd
import numpy as np
import json
from dotenv import load_dotenv
import os
import time

# Load environment variables
load_dotenv()

# Configuration
BASE_URL = "http://localhost:8000"
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

# Step 1: Create a sample DataFrame
def create_sample_df():
    """Create a sample DataFrame for testing with mixed data types"""
    # Create sample data
    data = {
        'order_id': [f'ORD-{i:04d}' for i in range(1, 101)],
        'customer_name': [f'Customer {i}' for i in range(1, 101)],
        'order_date': pd.date_range(start='2024-01-01', periods=100),
        'amount': np.random.uniform(50, 500, 100).round(2),
        'item_count': np.random.randint(1, 10, 100),
        'status': np.random.choice(['Pending', 'Shipped', 'Delivered', 'Cancelled'], 100),
        'payment_method': np.random.choice(['Credit Card', 'PayPal', 'Bank Transfer', 'Cash on Delivery'], 100),
        'notes': [f'Order note {i}' if i % 5 == 0 else None for i in range(1, 101)]
    }
    
    # Add some mixed data types to test detection
    mixed_data = []
    for i in range(100):
        if i < 30:
            mixed_data.append(i)
        elif i < 60:
            mixed_data.append(str(i))
        elif i < 90:
            mixed_data.append(f'Tag-{i}')
        else:
            mixed_data.append(None)
    
    data['mixed_column'] = mixed_data
    
    return pd.DataFrame(data)

# Step 2: Get a JWT token for authentication
def get_auth_token():
    """Get a JWT token for API authorization"""
    # For now, we'll assume you're logged in through Supabase already
    # and have stored the token in an environment variable
    token = os.getenv("SUPABASE_AUTH_TOKEN")
    
    if not token:
        print("No auth token found. Please set SUPABASE_AUTH_TOKEN environment variable.")
        print("You can get this from localStorage.supabase.auth.token in the browser.")
        return None
    
    return token

# Step 3: Create a test project
def create_test_project(token):
    """Create a test project for analysis"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    project_data = {
        "name": "DataFrame Analysis Test",
        "persona": "Data Analyst",
        "context": "Testing the DataFrame analysis functionality",
        "industry": "E-Commerce"
    }
    
    response = requests.post(f"{BASE_URL}/api/projects", json=project_data, headers=headers)
    
    if response.status_code == 200:
        project = response.json()
        print(f"Created test project with ID: {project['id']}")
        return project
    else:
        print(f"Failed to create project: {response.text}")
        return None

# Step 4: Trigger analysis on a project
def analyze_project(project_id, token):
    """Trigger analysis on a project"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.post(f"{BASE_URL}/api/projects/{project_id}/analyze", headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(f"Analysis triggered for project {project_id}")
        print(json.dumps(result, indent=2))
        return result
    else:
        print(f"Failed to trigger analysis: {response.text}")
        return None

# Step 5: Send a data analysis query to test the analyze endpoint
def test_analyze_endpoint(project_id, token, df):
    """Test the analyze endpoint with a data query"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    # Convert DataFrame to records for JSON serialization
    df_records = df.to_dict(orient="records")
    
    analyze_data = {
        "messages": [
            {"role": "user", "content": "Show me summary statistics for the amount column"}
        ],
        "project_id": project_id,
        "dataframe": df_records,
        "persona": "Data Analyst",
        "industry": "E-Commerce",
        "business_context": "Testing DataFrame analysis"
    }
    
    print("Sending data analysis request...")
    response = requests.post(f"{BASE_URL}/api/analyze", json=analyze_data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print("Analysis response received:")
        print(json.dumps(result, indent=2))
        return result
    else:
        print(f"Failed to send analysis request: {response.text}")
        return None

# Step 6: Get project context to verify metadata
def get_project_context(project_id, token):
    """Get project context to verify analysis metadata was saved"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.get(f"{BASE_URL}/api/projects/{project_id}/context", headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print("Project context retrieved:")
        
        # Check for data_analysis metadata in the project
        project_data = result.get("project", {})
        metadata = project_data.get("data_analysis", {})
        
        if metadata:
            print("Found data analysis metadata:")
            print(json.dumps(metadata, indent=2))
        else:
            print("No data analysis metadata found in project.")
            
        return result
    else:
        print(f"Failed to get project context: {response.text}")
        return None

# Main test function
def main():
    # Create sample DataFrame
    df = create_sample_df()
    print(f"Created sample DataFrame with {len(df)} rows and {df.columns.tolist()} columns")
    
    # Get auth token
    token = get_auth_token()
    if not token:
        return
    
    # Create test project
    project = create_test_project(token)
    if not project:
        return
    
    project_id = project["id"]
    
    # Send direct data analysis request with DataFrame
    # This should trigger our analysis code internally
    analysis_result = test_analyze_endpoint(project_id, token, df)
    
    # Give the server some time to process the analysis
    print("Waiting for analysis to complete...")
    time.sleep(5)
    
    # Get project context to verify metadata was saved
    context = get_project_context(project_id, token)
    
    # You can also explicitly trigger analysis on the project
    # analyze_result = analyze_project(project_id, token)
    
    print("Test completed!")

if __name__ == "__main__":
    main()
