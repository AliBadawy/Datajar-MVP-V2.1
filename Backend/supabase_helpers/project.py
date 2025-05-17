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
    import traceback
    from utils.analyze_dataframe import ensure_json_serializable
    
    logger = logging.getLogger(__name__)
    logger.info(f"===== Starting metadata update for project {project_id} =====")
    
    # Ensure project_id is an integer
    try:
        project_id = int(project_id)
        logger.info(f"Using project ID: {project_id} (type: {type(project_id)})")
    except (TypeError, ValueError):
        logger.error(f"Invalid project_id type: {type(project_id)}, value: {project_id}")
        return False
    
    try:
        # Step 1: Get Supabase client
        supabase = get_supabase_client()
        
        # Step 2: Check if the project exists
        logger.info("Verifying project exists in database...")
        project_check = supabase.table("projects").select("id").eq("id", project_id).execute()
        
        if not project_check or not hasattr(project_check, 'data') or len(project_check.data) == 0:
            logger.error(f"❌ Project with ID {project_id} not found in database")
            return False
        else:
            logger.info(f"✅ Project ID {project_id} exists in database")
        
        # Step 3: Sanitize metadata to ensure JSON compatibility
        logger.info("Sanitizing metadata...")
        sanitized_metadata = ensure_json_serializable(metadata)
        
        # Step 4: Create a simplified update payload
        update_data = {}
        
        # Only include fields that exist in the metadata
        if "metadata" in sanitized_metadata:
            update_data["metadata"] = sanitized_metadata["metadata"]
            logger.info(f"Including metadata field with {len(sanitized_metadata['metadata'])} records")
            
        if "data_sources" in sanitized_metadata:
            update_data["data_sources"] = sanitized_metadata["data_sources"]
            logger.info(f"Including data_sources field: {sanitized_metadata['data_sources']}")
        
        # Verify the data can be serialized to JSON
        try:
            json_string = json.dumps(update_data)
            logger.info(f"✅ Update data successfully serialized ({len(json_string)} chars)")
        except Exception as json_err:
            logger.error(f"❌ Failed to serialize update data: {str(json_err)}")
            return False
        
        # Step 5: Perform the update with simplified, verified data
        logger.info(f"Executing update for project {project_id}...")
        
        try:
            # Test with a minimal query first
            test_response = supabase.table("projects").update({"updated_at": "now()"}).eq("id", project_id).execute()
            logger.info("Test update successful")
            
            # Now perform the actual update with our data
            response = supabase.table("projects").update(update_data).eq("id", project_id).execute()
            
            if response and hasattr(response, 'data') and response.data:
                logger.info(f"✅ Successfully updated project {project_id}")
                return True
            else:
                logger.error("❌ Update operation failed - no data returned")
                if hasattr(response, 'error'):
                    logger.error(f"Error: {response.error}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Exception during update: {str(e)}")
            logger.error(traceback.format_exc())
            return False
            
    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}")
        logger.error(traceback.format_exc())
        return False
