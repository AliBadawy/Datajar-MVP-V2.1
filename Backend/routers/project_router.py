from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from models.schemas import ProjectCreateRequest, ProjectResponse
from supabase_helpers.project import insert_project, get_project_by_id
from supabase_helpers.messages import get_messages_by_project_id
from supabase_helpers.salla_order import get_salla_orders_for_project
from utils.supabase_client import get_supabase_client

router = APIRouter()

@router.post("/api/projects", response_model=ProjectResponse)
def create_project(project: ProjectCreateRequest):
    try:
        saved_project = insert_project(project)
        return saved_project
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating project: {str(e)}")
        
@router.get("/api/projects", response_model=List[ProjectResponse])
def get_projects():
    """
    Retrieve all projects from the database.
    """
    try:
        # Get Supabase client
        supabase = get_supabase_client()
        
        # Query the projects table
        response = supabase.table('projects').select("*").order("created_at", desc=True).execute()
        
        # Check if we have data
        if not response.data:
            return []
            
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
        
@router.get("/api/project/{project_id}/context")
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
        # Get project metadata
        project = get_project_by_id(project_id)
        if not project:
            raise HTTPException(status_code=404, detail=f"Project with ID {project_id} not found")
        
        # Get messages for this project
        messages = get_messages_by_project_id(project_id)
        
        # Get Salla data if available
        salla_df = get_salla_orders_for_project(project_id)
        has_data = salla_df is not None and not salla_df.empty
        
        # Put everything together
        result = {
            "project": project,
            "messages": messages,
            "has_data": has_data,
        }
        
        # Add data preview if available
        if has_data:
            result["data_preview"] = salla_df.head(100).to_dict(orient="records")
            result["columns"] = salla_df.columns.tolist()
            result["data_summary"] = {
                "total_rows": len(salla_df),
                "total_columns": len(salla_df.columns),
                "memory_usage": str(salla_df.memory_usage(deep=True).sum() / (1024 * 1024)) + " MB"
            }
        
        return result
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error getting project context: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching project context: {str(e)}")
