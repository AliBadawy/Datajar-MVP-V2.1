"""
Salla OAuth configuration utilities.
Provides helper functions to access Salla OAuth credentials from environment variables.
"""

import os
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

def get_salla_auth_url():
    """
    Returns the Salla OAuth authorization URL from environment variables.
    
    Returns:
        str: The Salla authorization URL
    """
    return os.getenv("SALLA_AUTH_URL")

def get_salla_client_id():
    """
    Returns the Salla client ID from environment variables.
    
    Returns:
        str: The Salla client ID
    """
    return os.getenv("SALLA_CLIENT_ID")

def get_salla_redirect_uri():
    """
    Returns the Salla redirect URI from environment variables.
    
    Returns:
        str: The redirect URI for Salla OAuth flow
    """
    return os.getenv("SALLA_REDIRECT_URI")

def get_salla_token_url():
    """
    Returns the Salla token URL from environment variables.
    
    Returns:
        str: The Salla token URL for exchanging authorization code
    """
    return os.getenv("SALLA_TOKEN_URL")

def get_salla_client_secret():
    """
    Returns the Salla client secret from environment variables.
    
    Returns:
        str: The Salla client secret
    """
    return os.getenv("SALLA_CLIENT_SECRET")
