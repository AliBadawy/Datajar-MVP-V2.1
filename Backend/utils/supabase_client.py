import os
from dotenv import load_dotenv
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Patch the httpx SyncClient to remove the proxy option
# This is needed because our version of Supabase tries to use proxy but httpx doesn't support it
import httpx
original_init = httpx.Client.__init__

def patched_init(self, *args, **kwargs):
    # Remove 'proxy' from kwargs if present
    if 'proxy' in kwargs:
        logger.info("Removing 'proxy' argument from httpx.Client initialization")
        del kwargs['proxy']
    return original_init(self, *args, **kwargs)

# Apply the patch
httpx.Client.__init__ = patched_init

# Now import supabase after patching httpx
from supabase import create_client, Client

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
        logger.info(f"Creating Supabase client for URL: {supabase_url[:10]}...")
        client = create_client(supabase_url, supabase_key)
        logger.info("Supabase client created successfully")
        return client
    except Exception as e:
        logger.error(f"Failed to create Supabase client: {str(e)}")
        raise
