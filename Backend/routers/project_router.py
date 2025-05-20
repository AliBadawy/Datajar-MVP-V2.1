from fastapi import APIRouter, HTTPException, Depends, Header
from typing import List, Dict, Any, Optional
from models.schemas import ProjectCreateRequest, ProjectResponse
from supabase_helpers.project import get_project_by_id, insert_project, get_project_metadata
from supabase_helpers.messages import get_messages_by_project_id
from supabase_helpers.salla_order import get_salla_orders_for_project
from utils.supabase_client import get_supabase_client
from auth.auth_handler import get_current_user

router = APIRouter()

@router.post("/projects", response_model=ProjectResponse)
async def create_project(project: ProjectCreateRequest, user: Dict = Depends(get_current_user)):
    try:
        print(f"Creating project with data: {project.dict()}")
        print(f"Authenticated user: {user}")
        
        # Always use the user_id from the token for security
        project.user_id = user["user_id"]
        print(f"Setting project user_id to: {project.user_id}")
        
        saved_project = insert_project(project)
        print(f"Project created successfully: {saved_project}")
        return saved_project
    except Exception as e:
        print(f"Error creating project: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating project: {str(e)}")
        
@router.get("/projects", response_model=List[ProjectResponse])
async def get_projects(user: Dict = Depends(get_current_user)):
    """
    Retrieve projects from the database, filtered by user_id from authentication token.
    """
    try:
        # Get Supabase client
        supabase = get_supabase_client()
        
        # Get user_id from token
        user_id = user["user_id"]
        print(f"Fetching projects for user: {user_id}")
        
        # Query the projects table with explicit user_id filter
        response = supabase.table('projects')\
            .select("*")\
            .eq("user_id", user_id)\
            .order("created_at", desc=True)\
            .execute()
        
        # Check if we have data
        if not response.data:
            print(f"No projects found for user: {user_id}")
            return []
        
        print(f"Found {len(response.data)} projects for user: {user_id}")
        for project in response.data:
            print(f"Project: {project['id']} - User: {project.get('user_id', 'None')}")
            
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching projects: {str(e)}")
        
@router.get("/projects/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int):
    """
    Retrieve a specific project by ID.
    """
    try:
        # Get Supabase client
        supabase = get_supabase_client()
        
        # Query the projects table for the specific project
        response = supabase.table('projects').select("*").eq("id", project_id).execute()
        
        # Check if we have data
        if not response.data:
            raise HTTPException(status_code=404, detail=f"Project with ID {project_id} not found")
            
        return response.data[0]
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching project: {str(e)}")
        
@router.get("/projects/{project_id}/context")
def get_project_context(project_id: int):
    """
    Retrieve the full context for a project including:
    - Project metadata (persona, industry, context)
    - All saved chat messages
    - Any uploaded data (e.g. from Salla, CSV, etc.) as a DataFrame preview
    
    Args:
        project_id (int): The ID of the project to retrieve context for
        
    Returns:
        dict: A dictionary containing project data, messages, and DataFrame info
    """
    # Initialize result with debug information
    result = {
        "_debug": {
            "steps_completed": [],
            "errors": []
        }
    }
    
    try:
        # Step 1: Get project basic info
        try:
            project = get_project_by_id(project_id)
            if not project:
                raise HTTPException(status_code=404, detail=f"Project with ID {project_id} not found")
            result["project"] = project
            result["_debug"]["steps_completed"].append("project_basic_info")
        except Exception as e:
            error_msg = f"Error getting project basic info: {str(e)}"
            print(error_msg)
            result["_debug"]["errors"].append({"step": "project_basic_info", "error": error_msg})
            # Set a default empty project
            result["project"] = {"id": project_id, "name": "Unknown", "description": "Error loading project details"}
        
        # Step 2: Get project metadata from the project_metadata table
        try:
            project_metadata = get_project_metadata(project_id)
            print(f"Loaded project metadata: {project_metadata is not None}")
            result["project_metadata"] = project_metadata["metadata"] if project_metadata else None
            result["data_sources"] = project_metadata["data_sources"] if project_metadata else []
            result["_debug"]["steps_completed"].append("project_metadata")
        except Exception as e:
            error_msg = f"Error getting project metadata: {str(e)}"
            print(error_msg)
            result["_debug"]["errors"].append({"step": "project_metadata", "error": error_msg})
            # Set defaults if this step fails
            result["project_metadata"] = None
            result["data_sources"] = []
        
        # Step 3: Get messages for this project - load complete message history
        try:
            messages = get_messages_by_project_id(project_id)
            print(f"Loaded {len(messages)} messages for project")
            result["messages"] = messages
            result["_debug"]["steps_completed"].append("messages")
        except Exception as e:
            error_msg = f"Error getting messages: {str(e)}"
            print(error_msg)
            result["_debug"]["errors"].append({"step": "messages", "error": error_msg})
            # Set empty messages if this fails
            result["messages"] = []
        
        # Step 4: Get Salla data if available - load the full DataFrame
        try:
            salla_df = get_salla_orders_for_project(project_id)
            has_data = salla_df is not None and not salla_df.empty
            print(f"Loaded Salla data: {has_data}, {len(salla_df) if has_data else 0} rows")
            result["has_data"] = has_data
            result["_debug"]["steps_completed"].append("salla_data")
            
            # Step 5: Generate DataFrame analysis if data is available
            if has_data:
                try:
                    from utils.analyze_dataframe import analyze_dataframe
                    data_analysis = analyze_dataframe(salla_df)
                    print(f"Generated data analysis with {len(data_analysis.keys()) if data_analysis else 0} metrics")
                    result["data_analysis"] = data_analysis
                    result["_debug"]["steps_completed"].append("data_analysis")
                    
                    # Add data preview - limit to just 20 rows for better performance
                    try:
                        result["data_preview"] = salla_df.head(20).to_dict(orient="records")
                        result["columns"] = salla_df.columns.tolist()
                        result["_debug"]["steps_completed"].append("data_preview")
                    except Exception as preview_error:
                        error_msg = f"Error creating data preview: {str(preview_error)}"
                        print(error_msg)
                        result["_debug"]["errors"].append({"step": "data_preview", "error": error_msg})
                except Exception as e:
                    error_msg = f"Error analyzing DataFrame: {str(e)}"
                    print(error_msg)
                    result["_debug"]["errors"].append({"step": "data_analysis", "error": error_msg})
                    # Skip data analysis if it fails
                    result["data_analysis"] = None
            else:
                result["data_analysis"] = None
        except Exception as e:
            error_msg = f"Error getting Salla data: {str(e)}"
            print(error_msg)
            result["_debug"]["errors"].append({"step": "salla_data", "error": error_msg})
            # Set defaults if this step fails
            result["has_data"] = False
            result["data_analysis"] = None
        
        # Return whatever data we were able to collect
        return result
    except Exception as outer_e:
        # Catch any other unexpected errors
        error_msg = f"Unexpected error in get_project_context: {str(outer_e)}"
        print(error_msg)
        if "_debug" not in result:
            result["_debug"] = {"steps_completed": [], "errors": []}
        result["_debug"]["errors"].append({"step": "outer_try_catch", "error": error_msg})
        return result
