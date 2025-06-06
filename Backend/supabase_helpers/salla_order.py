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
    try:
        # Call get_project_by_id instead of get_or_create_project since we only have the ID
        from supabase_helpers.project import get_project_by_id
        project = get_project_by_id(project_id)
        
        if not project:
            print(f"WARNING: Project with ID {project_id} not found. Creating placeholder.")
            # Create a minimal project data dict with the ID
            project = {'id': project_id, 'name': f'Project {project_id}'}
        
        print(f"Saving orders for project ID: {project_id} (Project name: {project.get('name', 'UNKNOWN')})")
    except Exception as e:
        print(f"Error retrieving project {project_id}: {str(e)}")
        # Continue with a minimal project object
        project = {'id': project_id, 'name': f'Project {project_id}'}
    
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
            # First, check if the salla_orders table exists and has the expected schema
            try:
                print("Checking if salla_orders table exists...")
                table_info = supabase.table("salla_orders").select("id").limit(1).execute()
                print(f"Table check result: {table_info}")
            except Exception as table_e:
                print(f"ERROR: Issue with table access. Table may not exist: {str(table_e)}")
                # Let's create the table if it doesn't exist
                try:
                    print("Attempting to create salla_orders table...")
                    # This would typically be done via migrations, but for debugging we'll try here
                    # This is just a diagnostic message - the actual table creation would be done
                    # through Supabase dashboard or migration scripts
                    print("IMPORTANT: Please create the salla_orders table in Supabase with these columns:")
                    print("- id (auto-incrementing primary key)")
                    print("- project_id (integer, required)")
                    print("- order_id (text)")
                    print("- status (text)")
                    print("- total_amount (numeric)")
                    print("- currency (text)")
                    print("- item_name (text)")
                    print("- item_quantity (numeric)")
                    print("- payment_method (text)")
                    print("- order_date (timestamp)")
                    print("- created_at (timestamp with default now())")
                    
                    # Return error message since we can't create the table here
                    return {
                        "success": False,
                        "error": "salla_orders table does not exist",
                        "message": "Please create the salla_orders table in Supabase"
                    }
                except Exception as create_e:
                    print(f"Failed to create table: {str(create_e)}")
                    raise create_e
            
            # Check for existing orders for this project
            try:
                existing = supabase.table("salla_orders").select("id").eq("project_id", project_id).execute()
                existing_count = len(existing.data) if existing.data else 0
                
                if existing_count > 0:
                    print(f"Found {existing_count} existing orders for project {project_id}. Replacing them.")
                    delete_response = supabase.table("salla_orders").delete().eq("project_id", project_id).execute()
                    print(f"Delete response: {delete_response}")
            except Exception as del_e:
                print(f"Error checking/deleting existing orders: {str(del_e)}")
                # Continue anyway to try the insert
            
            # Insert the new orders in smaller batches to avoid payload size limits
            batch_size = 100  # Process 100 records at a time
            total_inserted = 0
            insert_results = []
            
            for i in range(0, len(clean_rows), batch_size):
                batch = clean_rows[i:i+batch_size]
                print(f"Inserting batch {i//batch_size + 1}/{(len(clean_rows) + batch_size - 1)//batch_size} with {len(batch)} records")
                
                try:
                    batch_response = supabase.table("salla_orders").insert(batch).execute()
                    insert_results.append(batch_response)
                    
                    if batch_response.data:
                        total_inserted += len(batch_response.data)
                        print(f"Successfully inserted batch with {len(batch_response.data)} records")
                    else:
                        print(f"Warning: Batch insert returned no data. Response: {batch_response}")
                except Exception as batch_e:
                    print(f"Error inserting batch: {str(batch_e)}")
                    # Print the first record that caused issues
                    if batch:
                        print(f"First record in problematic batch: {batch[0]}")
                    # Continue with the next batch
            
            if total_inserted > 0:
                print(f"Successfully saved {total_inserted} Salla orders for project {project_id}")
                return {
                    "success": True,
                    "count": total_inserted,
                    "message": f"Successfully saved {total_inserted} Salla orders",
                    "project_id": project_id,
                    "project_name": project.get("name", "UNKNOWN")
                }
            else:
                raise Exception(f"No records were inserted successfully out of {len(clean_rows)} records")
            
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
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"📊 Retrieving Salla orders for project ID: {project_id}")
    
    # First check if orders are in the memory store
    if project_id in salla_orders_session_store:
        logger.info(f"Using cached orders from memory store for project ID: {project_id}")
        return salla_orders_session_store[project_id]
    
    # If not in memory, retrieve from Supabase
    try:
        logger.info(f"Querying Supabase for Salla orders with project_id={project_id}")
        
        # Check if the salla_orders table exists
        try:
            # Just check if we can access the table at all
            table_check = supabase.table("salla_orders").select("id").limit(1).execute()
            logger.info(f"Salla orders table exists and contains {len(table_check.data) if table_check.data else 0} records in first row")
        except Exception as table_e:
            logger.error(f"⚠️ Error accessing salla_orders table: {str(table_e)}")
            return None
        
        # Proceed with the actual query for this project's orders
        response = supabase.table("salla_orders").select("*").eq("project_id", project_id).execute()
        
        logger.info(f"Query response contains {len(response.data) if response.data else 0} orders")
        
        if response.data and len(response.data) > 0:
            # Create DataFrame from Supabase response
            df = pd.DataFrame(response.data)
            
            # Log information about the DataFrame
            logger.info(f"✅ Successfully retrieved {len(df)} Salla orders for project {project_id}")
            logger.info(f"DataFrame columns: {df.columns.tolist()}")
            logger.info(f"First few order IDs: {df['order_id'].head(5).tolist() if 'order_id' in df.columns else 'No order_id column'}")
            
            # Store in memory for faster access next time
            salla_orders_session_store[project_id] = df
            
            return df
        else:
            logger.warning(f"⚠️ No Salla orders found for project {project_id} in database")
            
            # Try to list all project_ids that have orders to help debugging
            try:
                all_projects = supabase.table("salla_orders").select("project_id").execute()
                if all_projects.data:
                    unique_projects = set(item['project_id'] for item in all_projects.data if 'project_id' in item)
                    logger.info(f"Projects with Salla orders: {unique_projects}")
                else:
                    logger.info("No Salla orders found in database for any project")
            except Exception as list_e:
                logger.error(f"Error listing projects with Salla orders: {str(list_e)}")
            
            return None
    except Exception as e:
        logger.error(f"❌ Error retrieving Salla orders from Supabase: {str(e)}")
        return None

def get_projects_with_salla_orders() -> List[int]:
    """
    Get a list of project IDs that have Salla orders in the database
    
    Returns:
        List[int]: List of project IDs with Salla orders
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Query Supabase for all distinct project_ids in the salla_orders table
        response = supabase.table("salla_orders").select("project_id").execute()
        
        if response.data:
            # Extract unique project IDs
            project_ids = set()
            for item in response.data:
                if 'project_id' in item and item['project_id'] is not None:
                    project_ids.add(int(item['project_id']))
                    
            # Convert to sorted list for consistent output
            return sorted(list(project_ids))
        else:
            logger.info("No Salla orders found in the database")
            return []
    except Exception as e:
        logger.error(f"Error retrieving projects with Salla orders: {str(e)}")
        return []

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
