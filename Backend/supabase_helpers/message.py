from utils.supabase_client import get_supabase_client
from typing import List, Dict, Optional, Any

def save_message(project_id: int, role: str, content: str, intent: str) -> Dict[str, Any]:
    """
    Save a message to the Supabase messages table.
    
    Args:
        project_id (int): The ID of the project this message belongs to
        role (str): Either 'user' or 'assistant'
        content (str): The text content of the message
        intent (str): Either 'chat' or 'data_analysis'
    
    Returns:
        Dict: The saved message data from Supabase response
    """
    # Get Supabase client
    supabase = get_supabase_client()
    
    # Prepare data
    data = {
        "project_id": project_id,
        "role": role,
        "content": content,
        "intent": intent
    }
    
    # Insert message
    response = supabase.table("messages").insert(data).execute()
    
    # Check if insertion was successful
    if not response.data:
        raise Exception("Failed to save message")
    
    return response.data[0]

def get_messages_by_project(project_id: int, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    """
    Retrieve messages for a specific project with pagination.
    
    Args:
        project_id (int): The ID of the project to get messages for
        limit (int): Maximum number of messages to retrieve (defaults to 100)
        offset (int): Number of messages to skip (for pagination)
    
    Returns:
        List[Dict]: List of message objects formatted for the OpenAI API
    """
    try:
        # Get Supabase client
        supabase = get_supabase_client()
        
        # Query messages for the project
        response = supabase.table("messages") \
            .select("role, content") \
            .eq("project_id", project_id) \
            .order("created_at") \
            .limit(limit) \
            .offset(offset) \
            .execute()
        
        # Format messages for OpenAI API
        messages = []
        for msg in response.data or []:
            # Messages need to have the format {"role": "...", "content": "..."}
            messages.append({
                "role": msg["role"], 
                "content": msg["content"]
            })
            
        return messages
    except Exception as e:
        print(f"Error retrieving messages for project {project_id}: {str(e)}")
        return []
