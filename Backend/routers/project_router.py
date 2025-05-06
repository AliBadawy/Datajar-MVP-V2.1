from fastapi import APIRouter, HTTPException
from typing import List
from models.schemas import ProjectCreateRequest, ProjectResponse
from supabase_helpers.project import insert_project
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
