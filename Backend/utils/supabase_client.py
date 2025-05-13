import os
from dotenv import load_dotenv
from supabase import create_client, Client
import logging

# Configure logging
logger = logging.getLogger(__name__)

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
    
    try:
        # Create client with only the required parameters
        # This avoids the 'proxy' parameter issue
        return create_client(supabase_url, supabase_key)
    except TypeError as e:
        # Log the error for debugging
        logger.error(f"Error initializing Supabase client: {str(e)}")
        
        # If there's a TypeError about unexpected arguments (like 'proxy'),
        # we can try to create the client with a more direct approach
        from supabase._sync.client import SyncClient
        return SyncClient(supabase_url, supabase_key)
