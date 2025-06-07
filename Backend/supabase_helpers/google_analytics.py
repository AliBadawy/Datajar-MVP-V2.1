import pandas as pd
from typing import List, Dict, Any, Optional
from utils.supabase_client import get_supabase_client
import json
from datetime import datetime

# Get Supabase client
supabase = get_supabase_client()

def save_google_analytics_data(project_id: int, data: Dict[str, Any], start_date: str, end_date: str):
    """
    Save Google Analytics data to Supabase for a specific project
    
    Args:
        project_id (int): Project ID to associate with the GA data
        data (Dict[str, Any]): Dictionary containing the Google Analytics data
        start_date (str): Start date of the data range in YYYY-MM-DD format
        end_date (str): End date of the data range in YYYY-MM-DD format
        
    Returns:
        dict: Result of the insert operation
    """
    # Validate project_id
    if project_id is None or not isinstance(project_id, int) or project_id <= 0:
        error_msg = f"Invalid project_id: {project_id}. Must be a positive integer."
        print(error_msg)
        return {"success": False, "error": error_msg, "message": "Failed to save Google Analytics data: invalid project ID"}
    
    try:
        # Check if project exists
        from supabase_helpers.project import get_project_by_id
        project = get_project_by_id(project_id)
        
        if not project:
            print(f"WARNING: Project with ID {project_id} not found. Creating placeholder.")
            project = {'id': project_id, 'name': f'Project {project_id}'}
        
        print(f"Saving Google Analytics data for project ID: {project_id} (Project name: {project.get('name', 'UNKNOWN')})")
    except Exception as e:
        print(f"Error retrieving project {project_id}: {str(e)}")
        project = {'id': project_id, 'name': f'Project {project_id}'}
    
    # Create a record to store in Supabase
    ga_record = {
        'project_id': project_id,
        'start_date': start_date,
        'end_date': end_date,
        'metrics': json.dumps(data.get('metric_headers', [])),
        'dimensions': json.dumps(data.get('dimension_headers', [])),
        'data': json.dumps(data.get('rows', [])),
        'created_at': datetime.now().isoformat(),
    }
    
    try:
        # Debug: Print Supabase instance
        print(f"Supabase client exists: {supabase is not None}")
        print(f"Saving GA record: {json.dumps({k: str(v)[:100] + '...' if isinstance(v, str) and len(str(v)) > 100 else v for k, v in ga_record.items()})}")
        
        # Store in Supabase
        try:
            result = supabase.table('google_analytics_data').insert(ga_record).execute()
            print(f"Insert operation executed successfully")
        except Exception as insert_error:
            print(f"ERROR during Supabase insert: {str(insert_error)}")
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")
            return {"success": False, "error": str(insert_error), "message": "Failed during Supabase insert operation"}
        
        # Check for errors
        if hasattr(result, 'error') and result.error is not None:
            print(f"Error saving Google Analytics data: {result.error}")
            return {"success": False, "error": str(result.error)}
        
        count = len(result.data) if result.data else 0
        print(f"Insert successful, {count} records created")
        return {"success": True, "count": count, "message": f"Successfully saved Google Analytics data"}
    
    except Exception as e:
        print(f"Exception saving Google Analytics data: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return {"success": False, "error": str(e), "message": "Failed to save Google Analytics data due to an exception"}

def get_google_analytics_data_for_project(project_id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieve Google Analytics data for a specific project
    
    Args:
        project_id (int): Project ID to retrieve data for
        
    Returns:
        Optional[Dict[str, Any]]: Dictionary containing the Google Analytics data if available, None otherwise
    """
    try:
        # Query Supabase
        result = (
            supabase.table('google_analytics_data')
            .select('*')
            .eq('project_id', project_id)
            .order('created_at', desc=True)
            .limit(1)
            .execute()
        )
        
        # Check if we have data
        if not result.data:
            return None
        
        # Parse the JSON fields
        data = result.data[0]
        data['metrics'] = json.loads(data['metrics'])
        data['dimensions'] = json.loads(data['dimensions'])
        data['data'] = json.loads(data['data'])
        
        return data
    
    except Exception as e:
        print(f"Error retrieving Google Analytics data for project {project_id}: {str(e)}")
        return None

def get_projects_with_google_analytics_data() -> List[int]:
    """
    Get a list of project IDs that have Google Analytics data in the database
    
    Returns:
        List[int]: List of project IDs with Google Analytics data
    """
    try:
        # Query Supabase for distinct project IDs
        result = (
            supabase.table('google_analytics_data')
            .select('project_id')
            .execute()
        )
        
        # Extract project IDs
        if not result.data:
            return []
        
        project_ids = [item['project_id'] for item in result.data]
        return list(set(project_ids))  # Remove duplicates
    
    except Exception as e:
        print(f"Error getting projects with Google Analytics data: {str(e)}")
        return []

def delete_google_analytics_data_for_project(project_id: int) -> Dict[str, Any]:
    """
    Delete all Google Analytics data for a specific project
    
    Args:
        project_id (int): Project ID to delete data for
        
    Returns:
        dict: Result of the delete operation
    """
    try:
        # Delete from Supabase
        result = (
            supabase.table('google_analytics_data')
            .delete()
            .eq('project_id', project_id)
            .execute()
        )
        
        # Check for errors
        if hasattr(result, 'error') and result.error is not None:
            return {"success": False, "error": str(result.error)}
        
        count = len(result.data) if result.data else 0
        return {"success": True, "count": count, "message": f"Deleted {count} Google Analytics records"}
    
    except Exception as e:
        return {"success": False, "error": str(e), "message": "Failed to delete Google Analytics data"}
