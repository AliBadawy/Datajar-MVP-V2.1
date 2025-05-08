import pandas as pd
from typing import List, Dict, Any, Optional
from utils.supabase_client import get_supabase_client
import json
from supabase_helpers.project import get_or_create_project

# Get Supabase client
supabase = get_supabase_client()

# In-memory store for salla orders (temporary session-based storage)
# In production, this would likely be replaced with Redis or another distributed cache
salla_orders_session_store = {}

def save_salla_orders(project_id: int, df: pd.DataFrame):
    """
    Save Salla orders DataFrame to Supabase for a specific project
    
    Args:
        project_id (int): Project ID to associate with the orders
        df (pd.DataFrame): DataFrame containing the Salla orders
        
    Returns:
        dict: Result of the insert operation
    """
    # Validate project_id
    if project_id is None or not isinstance(project_id, int) or project_id <= 0:
        error_msg = f"Invalid project_id: {project_id}. Must be a positive integer."
        print(error_msg)
        return {"success": False, "error": error_msg, "message": "Failed to save orders: invalid project ID"}
    
    # Get or create the project in the database
    print(f"Getting or creating project with ID: {project_id}")
    project = get_or_create_project(project_id)
    
    print(f"Saving orders for project ID: {project_id} (Project name: {project.get('name', 'UNKNOWN')})")
    
    if df.empty:
        return {"count": 0, "message": "No orders to save"}
    
    # Store in memory for temporary access (store the full DataFrame)
    salla_orders_session_store[project_id] = df
    
    try:
        # Create a new DataFrame with only the columns that match the database schema
        # Map the DataFrame columns to the database columns
        mapped_df = pd.DataFrame()
        
        # Add project_id to all rows
        mapped_df['project_id'] = project_id
        
        # Map the order_id column
        if 'id' in df.columns:
            mapped_df['order_id'] = df['id']
        
        # Map other columns that exist in our database schema
        column_mapping = {
            'status': 'status',
            'total': 'total_amount',  # Assuming 'total' in DataFrame corresponds to 'total_amount' in DB
            'currency': 'currency',
            'items_names': 'item_name',
            'total_quantity': 'item_quantity',
            'payment_method': 'payment_method'
        }
        
        for df_col, db_col in column_mapping.items():
            if df_col in df.columns:
                mapped_df[db_col] = df[df_col]
        
        # Handle date column specially to ensure proper formatting
        if 'order_date' in df.columns:
            mapped_df['order_date'] = df['order_date'].apply(
                lambda x: x.isoformat() if pd.notna(x) else None
            )
        
        # Log what we're about to insert
        print(f"Prepared {len(mapped_df)} rows with columns: {mapped_df.columns.tolist()}")
        
        # Validate project_id column to ensure it's properly set
        if 'project_id' not in mapped_df.columns or mapped_df['project_id'].isna().any():
            print("WARNING: project_id column is missing or contains null values!")
            print(f"Setting all project_id values to {project_id}")
            mapped_df['project_id'] = project_id
        
        # Double check again to be absolutely sure
        if mapped_df['project_id'].isna().any():
            print("ERROR: project_id still contains null values after assignment!")
            # Force set all to project_id again
            mapped_df['project_id'] = mapped_df['project_id'].fillna(project_id)
        
        # Check for null values and replace them with None for valid JSON
        for col in mapped_df.columns:
            if mapped_df[col].isna().any():
                print(f"Warning: Found null values in column '{col}'. Replacing with None.")
                mapped_df[col] = mapped_df[col].where(pd.notna(mapped_df[col]), None)
        
        # Convert to records for insertion
        rows = mapped_df.to_dict(orient="records")
        
        # Debug: Print the first row to check the format
        if rows:
            print(f"Sample row being inserted: {rows[0]}")
        else:
            print("Warning: No rows to insert")
            return {
                "success": False,
                "message": "No rows to insert after mapping"
            }
        
        # Clean the data to ensure it's valid JSON
        clean_rows = []
        for row in rows:
            clean_row = {}
            for key, value in row.items():
                # Convert any non-serializable values to strings
                if pd.isna(value):
                    clean_row[key] = None
                elif isinstance(value, (int, float, str, bool, type(None))):
                    clean_row[key] = value
                else:
                    clean_row[key] = str(value)
                    
            # Double-check project_id is set
            if clean_row.get('project_id') is None:
                clean_row['project_id'] = project_id
                
            clean_rows.append(clean_row)
        
        print(f"Sending {len(clean_rows)} rows to Supabase")
        
        # Insert into database
        try:
            # First, check if we need to delete any existing orders for this project
            existing = supabase.table("salla_orders").select("id").eq("project_id", project_id).execute()
            existing_count = len(existing.data) if existing.data else 0
            
            if existing_count > 0:
                print(f"Found {existing_count} existing orders for project {project_id}. Replacing them.")
                supabase.table("salla_orders").delete().eq("project_id", project_id).execute()
            
            # Insert the new orders
            response = supabase.table("salla_orders").insert(clean_rows).execute()
            
            if not response.data:
                raise Exception(f"Insert operation returned no data. Response: {response}")
                
            print(f"Successfully saved {len(clean_rows)} Salla orders for project {project_id}")
            return {
                "success": True,
                "count": len(clean_rows),
                "message": f"Successfully saved {len(clean_rows)} Salla orders",
                "project_id": project_id,
                "project_name": project.get("name", "UNKNOWN")
            }
        except Exception as e:
            error_msg = f"Failed to save orders to database: {str(e)}"
            print(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "message": "Failed to save orders due to database error"
            }
    except Exception as e:
        print(f"Error saving Salla orders to Supabase: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to save Salla orders to database"
        }

def get_salla_orders_for_project(project_id: int) -> Optional[pd.DataFrame]:
    """
    Retrieve Salla orders for a specific project
    
    Args:
        project_id (int): Project ID to retrieve orders for
        
    Returns:
        Optional[pd.DataFrame]: DataFrame of orders if available, None otherwise
    """
    # First check if orders are in the memory store
    if project_id in salla_orders_session_store:
        return salla_orders_session_store[project_id]
    
    # If not in memory, retrieve from Supabase
    try:
        response = supabase.table("salla_orders").select("*").eq("project_id", project_id).execute()
        
        if response.data:
            # Create DataFrame from Supabase response
            df = pd.DataFrame(response.data)
            
            # Store in memory for faster access next time
            salla_orders_session_store[project_id] = df
            
            return df
        else:
            return None
    except Exception as e:
        print(f"Error retrieving Salla orders from Supabase: {str(e)}")
        return None

def delete_salla_orders_for_project(project_id: int) -> Dict[str, Any]:
    """
    Delete all Salla orders for a specific project
    
    Args:
        project_id (int): Project ID to delete orders for
        
    Returns:
        dict: Result of the delete operation
    """
    try:
        # Remove from memory store if present
        if project_id in salla_orders_session_store:
            del salla_orders_session_store[project_id]
        
        # Delete from Supabase
        result = supabase.table("salla_orders").delete().eq("project_id", project_id).execute()
        
        return {
            "success": True,
            "message": f"Successfully deleted Salla orders for project {project_id}"
        }
    except Exception as e:
        print(f"Error deleting Salla orders from Supabase: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to delete Salla orders from database"
        }
