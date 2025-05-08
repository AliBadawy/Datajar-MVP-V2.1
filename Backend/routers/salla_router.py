from fastapi import APIRouter, HTTPException
from models.schemas import SallaOrdersRequest
from utils.salla_helpers import get_salla_orders, normalize_salla_orders, convert_orders_to_df
from supabase_helpers.salla_order import save_salla_orders, get_salla_orders_for_project
import pandas as pd
import requests
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Log environment variables for debugging (redacting secrets)
print(f"SALLA_CLIENT_ID: {os.getenv('SALLA_CLIENT_ID')[:6]}****")
print(f"SALLA_REDIRECT_URI: {os.getenv('SALLA_REDIRECT_URI')}")
print(f"SALLA_AUTH_URL: {os.getenv('SALLA_AUTH_URL')}")
print(f"SALLA_TOKEN_URL: {os.getenv('SALLA_TOKEN_URL')}")  

router = APIRouter()

class SallaCallbackRequest(BaseModel):
    code: str
    state: str
    
class SallaCallbackWithDatesRequest(BaseModel):
    code: str
    from_date: str
    to_date: str
    project_id: int

@router.post("/api/salla/orders")
def fetch_salla_orders(request: SallaOrdersRequest):
    """
    Fetch orders from Salla API for the specified date range using the provided access token.
    
    Args:
        request (SallaOrdersRequest): Request containing access_token, from_date, and to_date
        
    Returns:
        dict: JSON response containing the list of orders
    """
    try:
        # Get orders from Salla API
        orders = get_salla_orders(
            access_token=request.access_token,
            from_date=request.from_date,
            to_date=request.to_date
        )
        
        # Return raw orders as requested in this step
        return {"orders": orders}
    except Exception as e:
        # Log the error for debugging
        print(f"Error fetching Salla orders: {str(e)}")
        
        # Return error to client
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/salla/orders/df")
def fetch_orders_dataframe(request: SallaOrdersRequest):
    """
    Fetch orders from Salla API and convert them to a pandas DataFrame for analysis.
    
    Args:
        request (SallaOrdersRequest): Request containing access_token, from_date, to_date and project_id
        
    Returns:
        dict: JSON response with columns and rows for dataframe representation
    """
    try:
        # Validate project_id first
        if not request.project_id or request.project_id <= 0:
            return {
                "success": False,
                "error": f"Invalid project ID: {request.project_id}",
                "message": "Please provide a valid project ID"
            }
            
        # Validate date parameters
        try:
            from datetime import datetime
            # Check if dates are in correct format (YYYY-MM-DD)
            datetime.strptime(request.from_date, "%Y-%m-%d")
            datetime.strptime(request.to_date, "%Y-%m-%d")
        except ValueError:
            return {
                "success": False,
                "error": "Invalid date format",
                "message": "Dates must be in YYYY-MM-DD format"
            }
            
        # Log detailed request information for debugging
        print(f"Salla orders request: project_id={request.project_id}, from={request.from_date}, to={request.to_date}")
        # First check if we already have this data in memory to avoid redundant API calls
        existing_df = get_salla_orders_for_project(request.project_id) 
        if existing_df is not None:
            print(f"Using existing data for project {request.project_id} from memory. {len(existing_df)} orders found.")
            return {
                "success": True,
                "cached": True,
                "order_count": len(existing_df),
                "date_range": {
                    "from": request.from_date,
                    "to": request.to_date
                },
                "columns": existing_df.columns.tolist(),
                "rows": existing_df.head(100).to_dict(orient="records"),
                "summary": {
                    "total_orders": len(existing_df),
                    "total_value": float(existing_df["total"].sum()) if "total" in existing_df.columns else 0,
                    "avg_order_value": float(existing_df["total"].mean()) if "total" in existing_df.columns else 0,
                    "total_items": int(existing_df["total_quantity"].sum()) if "total_quantity" in existing_df.columns else 0,
                    "status_counts": existing_df["status"].value_counts().to_dict() if "status" in existing_df.columns else {}
                }
            }
        
        # Debug: Log the start of the API call
        print(f"Fetching orders from Salla API for project {request.project_id} from {request.from_date} to {request.to_date}")
        
        # Get orders from Salla API
        orders = get_salla_orders(
            access_token=request.access_token,
            from_date=request.from_date,
            to_date=request.to_date
        )
        
        # Debug: Log the API response
        print(f"Received {len(orders)} orders from Salla API")
        
        # If no orders, return empty response
        if not orders:
            return {
                "success": True,
                "order_count": 0,
                "message": "No orders found for the specified date range"
            }
        
        # Debug: Log start of conversion
        print("Converting orders to DataFrame...")
        
        # Convert to DataFrame
        df = convert_orders_to_df(orders)
        
        # Debug: Log conversion result
        print(f"DataFrame created with {len(df)} rows and {len(df.columns)} columns")
        
        # Limit the number of rows we save to improve performance
        # Only for demonstration/testing - in production you'd want to save all data
        if len(df) > 1000:
            print(f"WARNING: Large dataset with {len(df)} rows. Limiting to 1000 rows for performance.")
            save_df = df.head(1000)  # Limit to 1000 rows to avoid performance issues
        else:
            save_df = df
        
        # Debug: Log start of save operation
        print(f"Saving {len(save_df)} orders to database...")
        
        # Save to database and in-memory store
        save_result = save_salla_orders(project_id=request.project_id, df=save_df)
        
        # Debug: Log save result
        print(f"Save result: {save_result}")
        
        # Return DataFrame in a JSON-friendly format
        return {
            "success": True,
            "order_count": len(df),
            "date_range": {
                "from": request.from_date,
                "to": request.to_date
            },
            "columns": df.columns.tolist(),
            "rows": df.head(100).to_dict(orient="records"),
            "save_result": save_result,
            "summary": {
                "total_orders": len(df),
                "total_value": float(df["total"].sum()) if "total" in df.columns else 0,
                "avg_order_value": float(df["total"].mean()) if "total" in df.columns else 0,
                "total_items": int(df["total_quantity"].sum()) if "total_quantity" in df.columns else 0,
                "status_counts": df["status"].value_counts().to_dict() if "status" in df.columns else {}
            }
        }
    except Exception as e:
        # Log the error for debugging
        print(f"Error creating DataFrame from Salla orders: {str(e)}")
        
        # Return error to client
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/salla/callback")
def handle_callback(request: SallaCallbackRequest):
    """
    Handle the OAuth callback from Salla and exchange the authorization code for tokens.
    
    Args:
        request (SallaCallbackRequest): Request containing the authorization code and state
        
    Returns:
        dict: JSON response containing access and refresh tokens
    """
    try:
        # Log request data for debugging (truncate code for security)
        print(f"Received callback with code: {request.code[:10]}... and state: {request.state[:10]}...")
        
        # Exchange code for tokens
        token_url = os.getenv("SALLA_TOKEN_URL", "https://accounts.salla.sa/oauth2/token")
        client_id = os.getenv("SALLA_CLIENT_ID")
        client_secret = os.getenv("SALLA_CLIENT_SECRET")
        redirect_uri = os.getenv("SALLA_REDIRECT_URI")
        
        # Verify we have all required configuration
        if not client_id or not client_secret or not redirect_uri:
            missing = []
            if not client_id: missing.append("SALLA_CLIENT_ID")
            if not client_secret: missing.append("SALLA_CLIENT_SECRET")
            if not redirect_uri: missing.append("SALLA_REDIRECT_URI")
            error_msg = f"Missing environment variables: {', '.join(missing)}"
            print(error_msg)
            raise HTTPException(status_code=500, detail=error_msg)
            
        print(f"Using client_id: {client_id[:6]}****")
        print(f"Using redirect_uri: {redirect_uri}")
        print(f"Token URL: {token_url}")
        
        token_data = {
            "grant_type": "authorization_code",
            "client_id": client_id,
            "client_secret": client_secret,
            "code": request.code,
            "redirect_uri": redirect_uri
        }
        
        # Make the token exchange request with detailed logging
        print("Sending token request...")
        
        response = requests.post(token_url, data=token_data)
        print(f"Token response status code: {response.status_code}")
        
        # Check for errors and provide detailed feedback
        if response.status_code != 200:
            error_detail = f"Salla API error: Status {response.status_code}"
            try:
                error_json = response.json()
                error_detail = f"Salla API error: {error_json}"
            except Exception:
                error_detail = f"Salla API error: {response.text}"
                
            print(f"Token exchange error: {error_detail}")
            raise HTTPException(status_code=response.status_code, detail=error_detail)
            
        response_data = response.json()
        print("Token exchange successful")
        
        # Return tokens to client with redacted logging
        if 'access_token' in response_data:
            token_preview = response_data['access_token'][:10] + '****'
            print(f"Returning access token: {token_preview}")
        
        return response_data
    except HTTPException as he:
        # Re-raise HTTP exceptions
        raise he
    except Exception as e:
        # Log detailed error and return a user-friendly message
        print(f"Unexpected error in Salla callback: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Authentication error: {str(e)}")

@router.post("/api/salla/callback/data")
def handle_callback_with_data(request: SallaCallbackWithDatesRequest):
    """
    Handle the OAuth callback from Salla, exchange the authorization code for tokens,
    and immediately fetch and store the orders data.
    
    Args:
        request (SallaCallbackWithDatesRequest): Request containing the authorization code,
            date range, and project ID
        
    Returns:
        dict: JSON response indicating success status and order count
    """
    try:
        # Exchange code for tokens
        token_url = "https://accounts.salla.sa/oauth2/token"
        
        token_data = {
            "grant_type": "authorization_code",
            "client_id": os.getenv("SALLA_CLIENT_ID"),
            "client_secret": os.getenv("SALLA_CLIENT_SECRET"),
            "code": request.code,
            "redirect_uri": os.getenv("SALLA_REDIRECT_URI")
        }
        
        token_response = requests.post(token_url, data=token_data)
        token_response.raise_for_status()
        token_data = token_response.json()
        
        # Fetch orders using the access token
        orders = get_salla_orders(
            access_token=token_data["access_token"],
            from_date=request.from_date,
            to_date=request.to_date
        )
        
        # Convert to DataFrame
        df = convert_orders_to_df(orders)
        
        # Save to database
        save_result = save_salla_orders(project_id=request.project_id, df=df)
        
        # Return success response
        return {
            "success": True,
            "token_data": {
                "access_token": token_data["access_token"],
                "refresh_token": token_data.get("refresh_token"),
                "expires_in": token_data.get("expires_in"),
                "merchant": token_data.get("merchant")
            },
            "orders_count": len(df),
            "save_result": save_result
        }
    except Exception as e:
        print(f"Error in Salla callback with data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
        
        # Return DataFrame in a JSON-friendly format
        return {
            "success": True,
            "order_count": len(df),
            "date_range": {
                "from": request.from_date,
                "to": request.to_date
            },
            "columns": df.columns.tolist(),
            "rows": df.head(100).to_dict(orient="records"),
            "save_result": save_result,
            "summary": {
                "total_orders": len(df),
                "total_value": float(df["total"].sum()) if "total" in df.columns else 0,
                "avg_order_value": float(df["total"].mean()) if "total" in df.columns else 0,
                "total_items": int(df["total_quantity"].sum()) if "total_quantity" in df.columns else 0,
                "status_counts": df["status"].value_counts().to_dict() if "status" in df.columns else {}
            }
        }
        
    except Exception as e:
        # Log the error for debugging
        print(f"Error creating DataFrame from Salla orders: {str(e)}")
        
        # Return error to client
        raise HTTPException(status_code=500, detail=str(e))
