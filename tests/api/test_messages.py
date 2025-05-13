import pytest
import time

class TestMessages:
    """Test suite for message-related endpoints."""
    
    def test_send_message(self, test_client, auth_headers, test_project):
        """Test sending a message to the AI."""
        project_id = test_project["id"]
        
        message_data = {
            "content": "What insights can you provide from this dataset?",
            "project_id": project_id
        }
        
        response = test_client.post("/api/messages", json=message_data, headers=auth_headers)
        
        assert response.status_code in (200, 201, 202), f"Failed to send message: {response.text}"
        data = response.json()
        
        # Check response contains message ID
        assert "id" in data, "Response missing message ID"
        assert "content" in data, "Response missing message content"
        assert data["content"] == message_data["content"], "Message content in response doesn't match request"
        
        # Store message ID for later tests
        message_id = data["id"]
        return message_id
    
    def test_get_messages(self, test_client, auth_headers, test_project):
        """Test retrieving all messages for a project."""
        project_id = test_project["id"]
        
        # First, send a test message to ensure there's at least one
        message_data = {
            "content": "Test message for retrieval test",
            "project_id": project_id
        }
        test_client.post("/api/messages", json=message_data, headers=auth_headers)
        
        # Give the system a moment to process
        time.sleep(1)
        
        # Now retrieve messages
        response = test_client.get(f"/api/projects/{project_id}/messages", headers=auth_headers)
        
        assert response.status_code == 200, f"Failed to get messages: {response.text}"
        data = response.json()
        
        # Check response is a list
        assert isinstance(data, list), "Response should be a list of messages"
        # Should contain at least the message we just sent
        assert len(data) > 0, "No messages returned for project"
    
    def test_get_message_details(self, test_client, auth_headers, test_project):
        """Test retrieving details for a specific message."""
        project_id = test_project["id"]
        
        # First, send a test message
        message_data = {
            "content": "Test message for details test",
            "project_id": project_id
        }
        create_response = test_client.post("/api/messages", json=message_data, headers=auth_headers)
        assert create_response.status_code in (200, 201, 202), "Failed to create test message"
        
        message_id = create_response.json()["id"]
        
        # Give the system a moment to process
        time.sleep(1)
        
        # Now retrieve message details
        response = test_client.get(f"/api/messages/{message_id}", headers=auth_headers)
        
        assert response.status_code == 200, f"Failed to get message details: {response.text}"
        data = response.json()
        
        # Validate response matches the test message
        assert data["id"] == message_id, "Message ID in response doesn't match"
        assert data["content"] == message_data["content"], "Message content in response doesn't match"
    
    def test_ai_response(self, test_client, auth_headers, test_project):
        """Test that the AI responds to a message."""
        project_id = test_project["id"]
        
        # Send a message that should trigger an AI response
        message_data = {
            "content": "Please analyze this data and provide insights",
            "project_id": project_id
        }
        
        send_response = test_client.post("/api/messages", json=message_data, headers=auth_headers)
        assert send_response.status_code in (200, 201, 202), "Failed to send message"
        
        # Give AI time to respond (adjust based on your actual response times)
        time.sleep(5)
        
        # Get all messages for the project
        messages_response = test_client.get(f"/api/projects/{project_id}/messages", headers=auth_headers)
        assert messages_response.status_code == 200, "Failed to get messages"
        
        messages = messages_response.json()
        
        # Check if there's an AI response after our message
        user_message_found = False
        ai_response_found = False
        
        for message in messages:
            if user_message_found and message.get("role") == "assistant":
                ai_response_found = True
                break
            
            if message.get("content") == message_data["content"]:
                user_message_found = True
        
        # This might not pass if your AI system is async, adjust accordingly
        assert ai_response_found, "No AI response found after sending a message"
