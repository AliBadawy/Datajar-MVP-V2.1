from fastapi import APIRouter, HTTPException
from models.schemas import SallaOrdersRequest
from utils.salla_helpers import get_salla_orders, normalize_salla_orders, convert_orders_to_df
from supabase_helpers.salla_order import save_salla_orders, get_salla_orders_for_project
import pandas as pd
from typing import List, Dict, Any, Optional

router = APIRouter()

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
        request (SallaOrdersRequest): Request containing access_token, from_date, and to_date
        
    Returns:
        dict: JSON response with columns and rows for dataframe representation
    """
    try:
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
