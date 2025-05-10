from utils.supabase_client import get_supabase_client
from models.schemas import ProjectCreateRequest
from typing import Dict, Any, Optional

def insert_project(project: ProjectCreateRequest):
    try:
        supabase = get_supabase_client()
        response = supabase.table("projects").insert(project.dict()).execute()
        
        # Check if we have data in the response
        if not response.data:
            raise Exception("Failed to insert project: No data returned")
            
        return response.data[0]  # Return inserted row
    except Exception as e:
        raise Exception(f"Failed to insert project: {str(e)}")


def get_project_by_id(project_id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieve a project by its ID from Supabase.
    
    Args:
        project_id (int): The ID of the project to retrieve
        
    Returns:
        Optional[Dict[str, Any]]: The project data or None if not found
    """
    try:
        supabase = get_supabase_client()
        response = supabase.table("projects").select("*").eq("id", project_id).single().execute()
        return response.data
    except Exception as e:
        print(f"Error retrieving project {project_id}: {str(e)}")
        return None


def get_or_create_project(project_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Find a project by ID or create a new one if it doesn't exist.
    
    Args:
        project_data: Dictionary with project data, must include 'id' if looking up existing project
        
    Returns:
        Dict[str, Any]: The project data, either retrieved or newly created
    """
    try:
        # Check if we have an ID and try to get the project
        if 'id' in project_data and project_data['id']:
            existing_project = get_project_by_id(project_data['id'])
            if existing_project:
                return existing_project
        
        # Create a new project request object
        from models.schemas import ProjectCreateRequest
        
        project_request = ProjectCreateRequest(
            name=project_data.get('name', 'Untitled Project'),
            persona=project_data.get('persona', 'Data Analyst'),
            context=project_data.get('context', ''),
            industry=project_data.get('industry', 'E-Commerce'),
            user_id=project_data.get('user_id')
        )
        
        # Insert the new project
        return insert_project(project_request)
    except Exception as e:
        print(f"Error in get_or_create_project: {str(e)}")
        raise e
