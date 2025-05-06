import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Initialize the Supabase client
def get_supabase_client() -> Client:
    """
    Initialize and return a Supabase client using environment variables.
    
    Returns:
        Client: Supabase client instance
    """
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        raise ValueError("Missing Supabase credentials. Please check your .env file.")
    
    return create_client(supabase_url, supabase_key)
