from fastapi import APIRouter, HTTPException
from models.schemas import AnalyzeRequest
from supabase_helpers.message import save_message
from supabase_helpers.salla_order import get_salla_orders_for_project
from supabase_helpers.project import get_project_by_id
import logging
import pandas as pd
from typing import Dict, Any, Optional, List

# Configure logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import PandasAI handler
try:
    from handlers.pandasai_handler import analyze_with_pandasai
    PANDASAI_AVAILABLE = True
except ImportError:
    logger.warning("PandasAI not available. Install with 'pip install pandasai'")
    PANDASAI_AVAILABLE = False

router = APIRouter()

@router.post("/api/projects/{project_id}/analyze")
def analyze_project_data(project_id: int):
    """
    Endpoint to return static analysis data for a project and save it to the project_metadata table.
    
    Args:
        project_id: ID of the project to analyze
        
    Returns:
        dict: Static analysis data
    """
    try:
        # Retrieve project to ensure it exists
        project = get_project_by_id(project_id)
        if not project:
            raise HTTPException(status_code=404, detail=f"Project with id {project_id} not found")
            
        logger.info(f"Starting analysis for project {project_id}")
        
        # Check if Salla data exists for this project
        salla_data = None
        has_salla_data = False
        try:
            # Get Salla orders for this project
            salla_df = get_salla_orders_for_project(project_id)
            if salla_df is not None and not salla_df.empty:
                logger.info(f"Found Salla data for project {project_id} with {len(salla_df)} records")
                has_salla_data = True
                
                # Analyze the Salla dataframe to extract metadata
                from utils.analyze_dataframe import analyze_dataframe
                
                try:
                    # Pass the DataFrame to the analyze_dataframe function
                    salla_metadata = analyze_dataframe(salla_df)
                    logger.info(f"Successfully analyzed Salla data with {len(salla_df)} records")
                    logger.info(f"Extracted metadata: {list(salla_metadata.keys())}")
                except Exception as e:
                    logger.error(f"Error analyzing Salla data: {str(e)}")
                    salla_metadata = {"error": str(e)}
            else:
                logger.info(f"No Salla data found for project {project_id}")
        except Exception as e:
            logger.warning(f"Error checking Salla data: {str(e)}")
        
        # Determine data sources based on available data
        data_sources = []
        if has_salla_data:
            data_sources.append("Salla")
        
        # If no data source was found, return a clear message
        if not data_sources:
            logger.warning(f"No data sources found for project {project_id}")
            
            # Try to list available project IDs with data for debugging
            try:
                from supabase_helpers.salla_order import get_projects_with_salla_orders
                projects_with_orders = get_projects_with_salla_orders() or []
                if projects_with_orders:
                    logger.info(f"Projects with Salla orders: {projects_with_orders}")
                else:
                    logger.info("No projects with Salla orders found")
            except Exception as e:
                logger.error(f"Error checking projects with orders: {str(e)}")
            
            # Create a response indicating no data was found
            response_data = {
                "status": "no_data",
                "project_id": project_id,
                "summary": {
                    "sources": [],
                    "total_rows": 0
                },
                "message": f"No data found for project {project_id}. Please import data or use the copy-orders-to endpoint.",
                "metadata": {
                    "analyzed_at": None,
                    "data_sources": [],
                    "basic_stats": {
                        "total_records": 0,
                        "columns_analyzed": 0,
                        "missing_data_percentage": 0,
                    },
                    "column_details": {}
                }
            }
        else:
            # Create a response with the actual Salla metadata from the analysis
            response_data = {
                "status": "success",
                "project_id": project_id,
                "summary": {
                    "sources": data_sources,
                    "total_rows": len(salla_df) if salla_df is not None else 0
                },
                "metadata": {
                    "analyzed_at": "2025-05-17T12:00:00Z",
                    "data_sources": data_sources,
                    "analysis_results": salla_metadata  # Include the analysis results
                }
            }
        
        # Data for saving to Supabase in the new project_metadata table
        # Format the metadata to contain only the analysis results, not the entire response
        metadata_for_storage = {}
        
        if has_salla_data and 'analysis_results' in response_data.get('metadata', {}):
            # Store only the analysis results as metadata
            metadata_for_storage = response_data['metadata']['analysis_results']
            logger.info(f"Storing analyzed Salla data metadata with keys: {list(metadata_for_storage.keys())}")
        elif not data_sources or data_sources == ["Placeholder Data"]:
            # For placeholder data, store the basic metadata
            metadata_for_storage = response_data.get('metadata', {})
            logger.info("Storing placeholder metadata")
        
        # Prepare data for Supabase in the format expected by save_project_metadata
        supabase_data = {
            "metadata": metadata_for_storage,  # Store only the analysis metadata
            "data_sources": data_sources
        }
        
        # Save to Supabase using the new function
        try:
            from supabase_helpers.project import save_project_metadata
            logger.info(f"Saving analysis data to project_metadata table for project {project_id}")
            
            save_result = save_project_metadata(project_id, supabase_data)
            
            if not save_result:
                logger.warning(f"Failed to save metadata for project {project_id}")
            else:
                logger.info(f"✅ Analysis data successfully saved to Supabase for project {project_id}")
        except Exception as e:
            logger.error(f"Error saving to project_metadata table: {str(e)}")
            # Continue execution even if saving fails
            
        # Return the response to the frontend
        return response_data
    except Exception as e:
        logger.error(f"Error in analyze_project_data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error analyzing project data: {str(e)}")
    



@router.post("/api/classify")
def classify(request: AnalyzeRequest):
    """
    Endpoint to classify a user message as either 'chat' or 'data_analysis'.
    
    Args:
        request (AnalyzeRequest): An object containing a list of message objects
        
    Returns:
        dict: A dictionary with the 'intent' key containing the classification result
    """
    user_message = request.messages[-1]["content"]
    
    # Initialize DataFrame if available in the request
    df = None
    if request.dataframe:
        df = pd.DataFrame(request.dataframe)
        logger.info(f"Using DataFrame from request with {len(df)} rows for classification")
    # If no data in request but project_id is provided, try to get Salla data
    elif request.project_id:
        try:
            df = get_salla_orders_for_project(request.project_id)
            if df is not None and not df.empty:
                logger.info(f"Using Salla DataFrame for project {request.project_id} with {len(df)} rows for classification")
        except Exception as e:
            logger.warning(f"Error getting Salla data for classification: {str(e)}")
    
    # Call classify_user_prompt with the user message and DataFrame (if available)
    intent = classify_user_prompt(user_message, df)
    logger.info(f"Classified message as '{intent}' with {'dataset context' if df is not None else 'no dataset context'}")
    
    return {"intent": intent}

@router.post("/api/analyze")
def analyze(request: AnalyzeRequest):
    """
    Endpoint to analyze user queries using PandasAI with Salla orders data
    
    Args:
        request: AnalyzeRequest containing messages, project_id, and other context
        
    Returns:
        dict: Analysis response and available Salla data
    """
    # Log the request
    logger.info(f"Received analyze request: {request}")
    
    # Extract the user message from the request
    user_message = ""
    if request.messages:
        last_message = request.messages[-1]
        # Handle both object-style messages and dictionary messages
        if isinstance(last_message, dict):
            user_message = last_message.get("content", "")
        else:
            # Try attribute access if it's not a dict
            try:
                user_message = last_message.content
            except AttributeError:
                logger.warning(f"Unexpected message format: {type(last_message)}")
                # Fallback to string representation
                user_message = str(last_message)
    logger.info(f"User message: {user_message}")
    
    # Initialize response
    ai_response = f"I received your message: {user_message}"
    analysis_result = None
    
    # Get Salla data if a project_id is provided
    salla_data = None
    if request.project_id:
        try:
            # Try to get Salla orders for the project
            salla_data = get_salla_orders_for_project(request.project_id)
            if salla_data is not None and not salla_data.empty:
                logger.info(f"Found {len(salla_data)} Salla orders for project {request.project_id}")
                
                # Process the user query with PandasAI if available
                if PANDASAI_AVAILABLE and user_message:
                    try:
                        logger.info(f"Processing query with PandasAI: {user_message}")
                        
                        # Get previous messages for context (limit to last 5)
                        previous_messages = []
                        if len(request.messages) > 1:
                            for msg in request.messages[:-1][-5:]:
                                # Handle both object-style and dictionary messages
                                if isinstance(msg, dict):
                                    role = msg.get("role", "user")
                                    content = msg.get("content", "")
                                else:
                                    # Try attribute access for object-style messages
                                    try:
                                        role = "user" if getattr(msg, "role", "") == "user" else "assistant"
                                        content = getattr(msg, "content", "")
                                    except AttributeError:
                                        logger.warning(f"Unexpected message format: {type(msg)}")
                                        role = "user"  # default
                                        content = str(msg)  # fallback
                                
                                previous_messages.append({
                                    "role": role,
                                    "content": content
                                })
                        
                        # Run analysis with PandasAI
                        analysis_result = analyze_with_pandasai(
                            df=salla_data, 
                            query=user_message,
                            conversation_context=previous_messages
                        )
                        
                        # Update response with PandasAI analysis result
                        if analysis_result and "response" in analysis_result:
                            ai_response = analysis_result["response"]
                            logger.info(f"PandasAI analysis successful")
                        else:
                            logger.warning("PandasAI returned empty or invalid response")
                            
                    except Exception as ai_error:
                        logger.error(f"Error during PandasAI analysis: {str(ai_error)}")
                        ai_response = f"I encountered an error while analyzing your data: {str(ai_error)}"
                else:
                    if not PANDASAI_AVAILABLE:
                        logger.warning("PandasAI not available for analysis")
                        ai_response = "I can't perform data analysis right now because PandasAI is not available. Please contact the administrator."
            else:
                logger.info(f"No Salla orders found for project {request.project_id}")
                ai_response = "I couldn't find any Salla orders data for this project. Please make sure you have imported your Salla data."
        except Exception as e:
            logger.error(f"Error retrieving Salla data: {str(e)}")
            ai_response = f"I encountered an error while retrieving your Salla data: {str(e)}"
            salla_data = None
    
    # Save messages to Supabase if project_id is provided
    if request.project_id:
        try:
            # Save user message
            save_message(
                project_id=request.project_id,
                role="user",
                content=user_message,
                intent="data_analysis"  # Using 'data_analysis' as the intent for PandasAI queries
            )
            
            # Extract just the message content if it's a JSON object
            if isinstance(ai_response, dict) and 'message' in ai_response:
                message_content = ai_response['message']
            else:
                message_content = str(ai_response)
            
            # Save assistant analysis response with just the message content
            save_message(
                project_id=request.project_id,
                role="assistant",
                content=message_content,
                intent="data_analysis"  # Using 'data_analysis' as the intent for PandasAI responses
            )
            
            logger.info(f"Saved messages for project {request.project_id}")
        except Exception as e:
            logger.error(f"Error saving messages: {str(e)}")
    
    # Prepare response with analysis message and Salla data
    response = {
        "message": ai_response,
        "salla_data": None,
        "analysis": None
    }
    

    return response
