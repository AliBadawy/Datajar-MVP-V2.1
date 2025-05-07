from fastapi import APIRouter, HTTPException
from supabase_helpers.message import get_messages_by_project
from typing import Optional, List, Dict, Any

router = APIRouter()

@router.get("/api/messages/{project_id}")
def get_project_messages(project_id: int, page: int = 1, limit: int = 100):
    """
    Retrieve message history for a specific project with pagination support.
    
    Args:
        project_id (int): ID of the project to get messages for
        page (int): Page number (starting from 1)
        limit (int): Number of messages per page (default: 100)
    
    Returns:
        dict: Dictionary containing messages and pagination metadata
    """
    try:
        # Calculate offset
        offset = (page - 1) * limit
        
        # Get messages
        messages = get_messages_by_project(
            project_id=project_id,
            limit=limit,
            offset=offset
        )
        
        # Return messages with pagination metadata
        return {
            "messages": messages,
            "pagination": {
                "page": page,
                "limit": limit,
                "has_more": len(messages) == limit  # If we got exactly the limit, there might be more
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching messages: {str(e)}")
