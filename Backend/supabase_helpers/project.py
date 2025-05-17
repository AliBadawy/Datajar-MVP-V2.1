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


def save_project_metadata(project_id: int, metadata: Dict[str, Any]) -> bool:
    """
    Save a project's metadata to the project_metadata table in Supabase.
    
    Args:
        project_id: The ID of the project to update
        metadata: Dictionary containing metadata to save
        
    Returns:
        bool: True if save was successful, False otherwise
    """
    import logging
    import json
    from utils.analyze_dataframe import ensure_json_serializable
    
    logger = logging.getLogger(__name__)
    logger.info(f"Saving metadata to project_metadata table for project {project_id}")
    
    try:
        # Ensure project_id is an integer
        project_id = int(project_id)
        
        # Get Supabase client
        supabase = get_supabase_client()
        
        # Verify project exists
        project_check = supabase.table("projects").select("id").eq("id", project_id).execute()
        if not project_check or not hasattr(project_check, 'data') or len(project_check.data) == 0:
            logger.error(f"Project with ID {project_id} not found in database")
            return False
            
        # Sanitize metadata to ensure JSON compatibility
        sanitized_metadata = ensure_json_serializable(metadata)
        
        # Extract data sources if available
        data_sources = sanitized_metadata.get("data_sources", [])
        
        # Check if record already exists for this project
        existing_record = supabase.table("project_metadata").select("id").eq("project_id", project_id).execute()
        
        if existing_record and hasattr(existing_record, 'data') and len(existing_record.data) > 0:
            # Update existing record
            logger.info(f"Updating existing metadata record for project {project_id}")
            response = supabase.table("project_metadata").update({
                "metadata": sanitized_metadata,
                "data_sources": data_sources,
                "updated_at": "now()"
            }).eq("project_id", project_id).execute()
        else:
            # Insert new record
            logger.info(f"Creating new metadata record for project {project_id}")
            response = supabase.table("project_metadata").insert({
                "project_id": project_id,
                "metadata": sanitized_metadata,
                "data_sources": data_sources
            }).execute()
        
        if response and hasattr(response, 'data') and response.data:
            logger.info(f"Successfully saved metadata for project {project_id}")
            return True
        else:
            logger.error("Failed to save metadata - no data returned")
            if hasattr(response, 'error'):
                logger.error(f"Error: {response.error}")
            return False
            
    except Exception as e:
        logger.error(f"Error saving project metadata: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def update_project_metadata(project_id: int, metadata: Dict[str, Any]) -> bool:
    """
    Update a project's metadata in Supabase (legacy function).
    This now calls save_project_metadata which uses the new table structure.
    
    Args:
        project_id: The ID of the project to update
        metadata: Dictionary containing metadata to update
        
    Returns:
        bool: True if update was successful, False otherwise
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Legacy update_project_metadata called, forwarding to save_project_metadata")
    
    # Call the new function that uses the project_metadata table
    return save_project_metadata(project_id, metadata)
