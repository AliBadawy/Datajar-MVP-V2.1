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
        
@router.get("/api/projects/{project_id}", response_model=ProjectResponse)
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
        
@router.get("/api/projects/{project_id}/context")
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
    try:
        # Get project basic info
        project = get_project_by_id(project_id)
        if not project:
            raise HTTPException(status_code=404, detail=f"Project with ID {project_id} not found")
        
        # Get project metadata from the project_metadata table
        project_metadata = get_project_metadata(project_id)
        print(f"Loaded project metadata: {project_metadata is not None}")
        
        # Get messages for this project - load complete message history
        messages = get_messages_by_project_id(project_id)
        print(f"Loaded {len(messages)} messages for project")
        
        # Get Salla data if available - load the full DataFrame
        salla_df = get_salla_orders_for_project(project_id)
        has_data = salla_df is not None and not salla_df.empty
        print(f"Loaded Salla data: {has_data}, {len(salla_df) if has_data else 0} rows")
        
        # Generate DataFrame analysis if data is available
        data_analysis = None
        if has_data:
            try:
                from utils.analyze_dataframe import analyze_dataframe
                data_analysis = analyze_dataframe(salla_df)
                print(f"Generated data analysis with {len(data_analysis.keys()) if data_analysis else 0} metrics")
            except Exception as e:
                print(f"Error analyzing DataFrame: {str(e)}")
                
        # Put everything together
        result = {
            "project": project,
            "messages": messages,
            "has_data": has_data,
            "project_metadata": project_metadata["metadata"] if project_metadata else None,
            "data_sources": project_metadata["data_sources"] if project_metadata else [],
            "data_analysis": data_analysis,
        }
        
        # Add data preview if available
        if has_data:
            # Add a limited preview of the actual data
            result["data_preview"] = salla_df.head(100).to_dict(orient="records")
            result["columns"] = salla_df.columns.tolist()
            
            # Add detailed summary
            result["data_summary"] = {
                "total_rows": len(salla_df),
                "total_columns": len(salla_df.columns),
                "memory_usage": str(salla_df.memory_usage(deep=True).sum() / (1024 * 1024)) + " MB",
                "data_types": {col: str(dtype) for col, dtype in salla_df.dtypes.items()},
                "missing_values": {col: int(salla_df[col].isna().sum()) for col in salla_df.columns}
            }
            
            # Add summary statistics for numeric columns
            try:
                numeric_stats = salla_df.describe().to_dict()
                result["numeric_stats"] = numeric_stats
            except Exception as e:
                print(f"Error generating numeric stats: {str(e)}")
        
        return result
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error getting project context: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching project context: {str(e)}")
