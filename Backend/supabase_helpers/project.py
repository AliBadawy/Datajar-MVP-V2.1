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


def get_or_create_project(project_id: int) -> Dict[str, Any]:
    """
    Get a project by ID, or create a default one if it doesn't exist.
    
    Args:
        project_id (int): The ID of the project to retrieve or create
        
    Returns:
        Dict[str, Any]: The project data
    """
    # First try to get the existing project
    project = get_project_by_id(project_id)
    
    if project:
        print(f"Found existing project: {project['name']} (ID: {project['id']})")
        return project
        
    # If project doesn't exist, get the first available project
    try:
        supabase = get_supabase_client()
        response = supabase.table("projects").select("*").limit(1).execute()
        
        if response.data and len(response.data) > 0:
            project = response.data[0]
            print(f"Using first available project: {project['name']} (ID: {project['id']})")
            return project
    except Exception as e:
        print(f"Error finding alternative project: {str(e)}")
    
    # If no projects exist, create a default one
    try:
        print("Creating default project...")
        from models.schemas import ProjectCreateRequest
        
        default_project = ProjectCreateRequest(
            name="Default Salla Project",
            persona="E-commerce Manager",
            context="Auto-created for Salla integration",
            industry="E-commerce"
        )
        
        new_project = insert_project(default_project)
        print(f"Created default project with ID: {new_project['id']}")
        return new_project
    except Exception as e:
        print(f"Error creating default project: {str(e)}")
        # Return a minimal project definition as fallback
        return {
            "id": project_id,
            "name": "Default Project",
            "persona": "Data Analyst",
            "context": "Auto-created",
            "industry": "E-commerce"
        }
