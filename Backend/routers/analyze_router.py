from fastapi import APIRouter, HTTPException
from models.schemas import AnalyzeRequest
from supabase_helpers.message import save_message
from handlers.openai_handler import simplified_prompt_handler, get_simple_response
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        
        # If no data source was found, use placeholder
        if not data_sources:
            data_sources = ["Placeholder Data"]
            logger.info("No data sources found, using placeholder data")
            
            # Create static placeholder data
            column_details = {
                "order_id": { "type": "string", "missing": 0 },
                "customer_name": { "type": "string", "missing": 3 },
                "amount": { "type": "numeric", "missing": 0 },
                "date": { "type": "datetime", "missing": 0 },
                "status": { "type": "string", "missing": 0 },
            }
            
            # Create a response object with placeholder data
            response_data = {
                "status": "success",
                "project_id": project_id,
                "summary": {
                    "sources": data_sources,
                    "total_rows": 120
                },
                "metadata": {
                    "analyzed_at": "2025-05-17T12:00:00Z",
                    "data_sources": data_sources,
                    "basic_stats": {
                        "total_records": 120,
                        "columns_analyzed": 5,
                        "missing_data_percentage": 2.5,
                    },
                    "column_details": column_details
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
    
    # Old implementation (keeping as reference)
    '''
    # Collect all available dataframes
    dataframes = []

    if salla_df is not None and not salla_df.empty:
        logger.info(f"Found Salla data for project {project_id} with {len(salla_df)} rows")
        dataframes.append(("Salla", salla_df))

    if csv_df is not None and not csv_df.empty:
        logger.info(f"Found CSV data for project {project_id} with {len(csv_df)} rows")
        dataframes.append(("CSV", csv_df))

    if not dataframes:
        logger.warning(f"No data available for analysis in project {project_id}")
        raise HTTPException(status_code=404, detail="No data available for analysis")

    # Process each dataframe and collect metadata
    metadata_results = []
    sources = []

    for source_name, df in dataframes:
        sources.append(source_name)
        # Use the new analyze_dataframe function
        from utils.analyze_dataframe import analyze_dataframe
        result = analyze_dataframe(df)
        
        metadata_results.append({
            "source": source_name,
            "total_rows": df.shape[0],
            "total_columns": df.shape[1],
            "columns": result.get("data_types"),
            "categorical_data": result.get("categorical_data"),
            "missing_data": result.get("missing_data"),
            "head": result.get("head_rows"),
            "date_parts": result.get("date_parts"),
            "numerical_stats": result.get("numerical_stats"),
            "inconsistent_columns": result.get("inconsistent_columns"),
        })

    # Save to Supabase
    try:
        from supabase_helpers.project import update_project_metadata
        logger.info(f"Attempting to save metadata to Supabase for project {project_id}")
        logger.info(f"Metadata contains {len(metadata_results)} source(s): {sources}")
        
        # Debug log the metadata structure (but not all content)
        for idx, meta in enumerate(metadata_results):
            logger.info(f"Source {idx+1}: {meta['source']} - {meta['total_rows']} rows, {meta['total_columns']} columns")
        
        update_result = update_project_metadata(project_id, {
            "metadata": metadata_results,
            "data_sources": sources
        })
        
        if not update_result:
            logger.error(f"❌ Failed to update metadata for project {project_id} - update_project_metadata returned False")
            raise HTTPException(status_code=500, detail="Failed to save project metadata: update operation returned False")
            
        logger.info(f"✅ Metadata successfully saved to Supabase for project {project_id}")
    except Exception as e:
        logger.error(f"❌ Exception when saving metadata to Supabase: {str(e)}")
        logger.error(f"Exception details: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to save project metadata: {str(e)}")

    logger.info(f"🎉 Analysis complete for project {project_id}")
    
    return {
        "status": "success",
        "project_id": project_id,
        "summary": {
            "sources": sources,
            "total_rows": sum(df.shape[0] for _, df in dataframes)
        }
    }
    '''


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
    Simplified endpoint that acknowledges user messages.
    
    Args:
        request (AnalyzeRequest): Object containing messages and context
        
    Returns:
        dict: Simple acknowledgment response
    """
    # Extract the last message from request
    if not request.messages or len(request.messages) == 0:
        raise HTTPException(status_code=400, detail="No messages provided")
    
    # Get the last message
    last_message = request.messages[-1]
    user_message = last_message["content"]
    
    # Log information about the request
    logger.info(f"Received message: '{user_message[:50]}...'")
    
    # Always classify as chat using the simplified handler
    intent = simplified_prompt_handler(user_message)
    
    # Get a simple response message
    response_text = get_simple_response(user_message)
    
    # Save user message to Supabase if project_id is provided
    if request.project_id:
        try:
            # Save user message
            save_message(
                project_id=request.project_id,
                role="user",
                content=user_message,
                intent=intent  # Will always be "chat"
            )
            
            # Save assistant response
            save_message(
                project_id=request.project_id,
                role="assistant",
                content=response_text,
                intent=intent  # Will always be "chat"
            )
            
            logger.info(f"Saved messages for project {request.project_id}")
        except Exception as e:
            logger.error(f"Error saving messages: {str(e)}")
            # Continue processing even if saving fails
    
    # Return a simple acknowledgment
    return {
        "type": "chat",
        "response": response_text
    }
