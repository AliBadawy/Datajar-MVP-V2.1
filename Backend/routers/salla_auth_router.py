from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
import os
import requests
from utils.salla_config import (
    get_salla_client_id,
    get_salla_client_secret,
    get_salla_redirect_uri,
    get_salla_token_url
)

router = APIRouter()

class CallbackRequest(BaseModel):
    code: str
    state: str

@router.post("/api/salla/callback")
def handle_salla_callback(payload: CallbackRequest):
    """
    Handle Salla OAuth callback by exchanging authorization code for access token.
    
    Args:
        payload (CallbackRequest): Object containing code and state from Salla OAuth redirect
        
    Returns:
        dict: JSON response containing access_token, refresh_token, etc.
    """
    code = payload.code
    state = payload.state  # You can validate this against a store/local memory

    # Get Salla configuration from environment variables
    client_id = get_salla_client_id()
    client_secret = get_salla_client_secret()
    redirect_uri = get_salla_redirect_uri()
    token_url = get_salla_token_url()
    
    if not all([client_id, client_secret, redirect_uri, token_url]):
        raise HTTPException(
            status_code=500, 
            detail="Missing Salla configuration. Check environment variables."
        )

    # Exchange code for token
    try:
        token_response = requests.post(token_url, data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": client_id,
            "client_secret": client_secret,
        })

        # Check if the token exchange was successful
        if token_response.status_code != 200:
            error_detail = f"Failed to exchange code: {token_response.text}"
            print(error_detail)
            raise HTTPException(status_code=401, detail=error_detail)

        # Return the token response JSON
        return token_response.json()  # access_token, refresh_token, expires_in, store_id etc.
    
    except requests.RequestException as e:
        print(f"Request error during token exchange: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error during token exchange: {str(e)}")
