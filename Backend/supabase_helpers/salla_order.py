import pandas as pd
from typing import List, Dict, Any, Optional
from utils.supabase_client import get_supabase_client

# Get the Supabase client
supabase = get_supabase_client()

# In-memory store for DataFrames (temporary session-based storage)
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
            clean_rows.append(clean_row)
        
        print(f"Cleaned {len(clean_rows)} rows for insertion")
        
        # Insert data into Supabase
        result = supabase.table("salla_orders").insert(clean_rows).execute()
        
        return {
            "success": True,
            "count": len(rows),
            "message": f"Successfully saved {len(rows)} Salla orders for project {project_id}"
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
