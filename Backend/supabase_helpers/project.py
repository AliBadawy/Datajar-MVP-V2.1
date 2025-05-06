from supabase import create_client
from models.schemas import ProjectCreateRequest
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def insert_project(project: ProjectCreateRequest):
    try:
        response = supabase.table("projects").insert(project.dict()).execute()
        
        # Check if we have data in the response
        if not response.data:
            raise Exception("Failed to insert project: No data returned")
            
        return response.data[0]  # Return inserted row
    except Exception as e:
        raise Exception(f"Failed to insert project: {str(e)}")
