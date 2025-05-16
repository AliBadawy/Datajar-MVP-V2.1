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


def update_project_metadata(project_id: int, metadata: Dict[str, Any]) -> bool:
    """
    Update a project's metadata in Supabase.
    
    Args:
        project_id: The ID of the project to update
        metadata: Dictionary containing metadata to update
        
    Returns:
        bool: True if update was successful, False otherwise
    """
    import logging
    import json
    
    logger = logging.getLogger(__name__)
    logger.info(f"Updating metadata for project {project_id}")
    
    try:
        # First, check if the metadata can be serialized to JSON
        try:
            # Attempt to serialize the metadata to verify it's valid JSON
            json_string = json.dumps(metadata)
            logger.info(f"Metadata successfully serialized to JSON ({len(json_string)} characters)")
        except (TypeError, ValueError, OverflowError) as json_err:
            logger.error(f"Failed to serialize metadata to JSON: {str(json_err)}")
            logger.error(f"Metadata keys: {list(metadata.keys())}")
            
            # Try to identify problematic fields
            for key, value in metadata.items():
                try:
                    json.dumps({key: value})
                except Exception as field_err:
                    logger.error(f"Problem field: '{key}', error: {str(field_err)}")
            return False
        
        # Connect to Supabase and update the project
        supabase = get_supabase_client()
        logger.info(f"Executing Supabase update for project {project_id}")
        
        # Format metadata for Supabase
        update_data = {}
        if "metadata" in metadata:
            update_data["metadata"] = metadata["metadata"]
        if "data_sources" in metadata:
            update_data["data_sources"] = metadata["data_sources"]
            
        response = supabase.table("projects").update(update_data).eq("id", project_id).execute()
        
        # Check if the update was successful
        if response and response.data:
            logger.info(f"Successfully updated metadata for project {project_id}")
            return True
        else:
            logger.error(f"Failed to update metadata for project {project_id}: No data in response")
            logger.error(f"Response: {response}")
            return False
    except Exception as e:
        logger.error(f"Exception updating project metadata: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False
