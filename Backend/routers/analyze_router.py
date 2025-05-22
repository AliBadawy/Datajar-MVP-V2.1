from fastapi import APIRouter, HTTPException
from models.schemas import AnalyzeRequest
from handlers.openai_handler import (
    get_openai_response,
    classify_user_prompt,
    wrap_pandasai_result_with_gpt
)
from handlers.pandasai_handler import initialize_smart_df, ask_pandasai
from handlers.dataframe_handler import analyze_and_store_project_data
from handlers.pandas_instruction_agent import generate_analysis_plan
from supabase_helpers.message import save_message, get_messages_by_project
from supabase_helpers.project import get_project_by_id, save_project_metadata
from supabase_helpers.salla_order import get_salla_orders_for_project
import pandas as pd
from typing import Optional, List, Dict, Any
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
    Endpoint that analyzes user messages and performs either chat or data analysis.
    
    Args:
        request (AnalyzeRequest): Object containing messages, optional dataframe, and context
        
    Returns:
        dict: Response with either chat content or data analysis results
    """
    # Fallback values from the request
    persona = request.persona
    industry = request.industry
    context = request.business_context
    history = request.messages
    project_analyzed = False  # Flag to track if data analysis has been run
    
    # Fetch project metadata and history if project_id is provided
    if request.project_id:
        # Get project metadata
        project = get_project_by_id(request.project_id)
        if project:
            # Override with project values if available
            persona = project.get("persona", persona)
            industry = project.get("industry", industry)
            context = project.get("context", context)
            
            # Fetch previous messages for this project
            db_messages = get_messages_by_project(request.project_id)
            
            # Merge previous messages with current request messages
            if db_messages:
                # Only append the latest user message to avoid duplication
                history = db_messages + [request.messages[-1]]
    
    # Initialize DataFrame if available in the request
    df = None
    if request.dataframe:
        try:
            # Check if we received a valid dataframe structure
            if isinstance(request.dataframe, list):
                # Handle list of records format
                df = pd.DataFrame(request.dataframe)
            elif isinstance(request.dataframe, dict):
                # Handle dict format with validation to ensure all columns have same length
                # First check if all arrays are the same length
                lengths = {k: len(v) for k, v in request.dataframe.items() if isinstance(v, list)}
                if lengths and len(set(lengths.values())) > 1:
                    # Different lengths, need to normalize
                    logger.warning(f"Received inconsistent column lengths: {lengths}")
                    max_len = max(lengths.values())
                    normalized_data = {}
                    for k, v in request.dataframe.items():
                        if isinstance(v, list):
                            # Pad shorter arrays with None
                            normalized_data[k] = v + [None] * (max_len - len(v))
                        else:
                            normalized_data[k] = v
                    df = pd.DataFrame(normalized_data)
                else:
                    # All good, create DataFrame normally
                    df = pd.DataFrame(request.dataframe)
            else:
                # Unknown format, create empty DataFrame
                logger.warning(f"Received dataframe in unknown format: {type(request.dataframe)}")
                df = pd.DataFrame()
            
            logger.info(f"Successfully created DataFrame with {len(df)} rows and {len(df.columns)} columns for intent classification")
        except Exception as e:
            logger.error(f"Error creating DataFrame from request: {str(e)}")
            # Create empty DataFrame instead of failing
            df = pd.DataFrame()
            logger.info("Created empty DataFrame after error")
            import traceback
            logger.error(traceback.format_exc())
    # If no data in request but project_id is provided, try to get Salla data
    elif request.project_id:
        try:
            df = get_salla_orders_for_project(request.project_id)
            if df is not None and not df.empty:
                logger.info(f"Found Salla DataFrame for project {request.project_id} with {len(df)} rows for intent classification")
        except Exception as e:
            logger.warning(f"Error getting Salla data for intent classification: {str(e)}")
            
    # 1. Determine if it's a chat message or a data analysis query
    last_message = request.messages[-1]
    intent = classify_user_prompt(last_message["content"], df)
    logger.info(f"Analyzed message: '{last_message['content'][:50]}...' classified as: {intent}")
    
    
    # Save user message to Supabase if project_id is provided
    if request.project_id:
        try:
            save_message(
                project_id=request.project_id,
                role="user",
                content=last_message["content"],
                intent=intent
            )
        except Exception as e:
            print(f"Error saving user message: {str(e)}")
            # Continue processing even if saving fails

    # 2. If it's a generic chat message or no data provided → GPT-only response
    if intent == "chat":
        # Initialize project metadata and data analysis
        project_metadata = None
        data_analysis = None
        
        # Try to get project metadata if project_id is available
        if request.project_id:
            try:
                from supabase_helpers.project import get_project_metadata
                project_metadata = get_project_metadata(request.project_id)
                logger.info(f"Loaded project metadata for chat: {project_metadata is not None}")
            except Exception as e:
                logger.warning(f"Error loading project metadata for chat: {str(e)}")
        
        # Generate DataFrame analysis if data is available
        if df is not None and not df.empty:
            try:
                from utils.analyze_dataframe import analyze_dataframe
                data_analysis = analyze_dataframe(df)
                logger.info(f"Generated data analysis for chat with {len(data_analysis.keys()) if data_analysis else 0} metrics")
            except Exception as e:
                logger.warning(f"Error analyzing DataFrame for chat: {str(e)}")
        
        # Call get_openai_response with all available context
        response = get_openai_response(
            messages=history, 
            persona=persona, 
            industry=industry, 
            business_context=context,
            project_metadata=project_metadata["metadata"] if project_metadata else None,
            data_analysis=data_analysis,
            df=df
        )
        
        # Save assistant response to Supabase if project_id is provided
        if request.project_id:
            try:
                save_message(
                    project_id=request.project_id,
                    role="assistant",
                    content=response,
                    intent="chat"
                )
            except Exception as e:
                print(f"Error saving assistant message: {str(e)}")
                # Continue processing even if saving fails
        
        return {"type": "chat", "response": response}

    # 3. Otherwise → Full data analysis flow
    elif intent == "data_analysis":
        # Initialize DataFrame
        df = None
        
        # If we have serialized data from the request, use that
        if request.dataframe:
            df = pd.DataFrame(request.dataframe)
            logger.info(f"Using DataFrame from request with {len(df)} rows and {len(df.columns)} columns")
        # If no data from request, try to get it from Salla for this project
        elif request.project_id:
            try:
                logger.info(f"Attempting to get Salla data for project_id: {request.project_id}")
                
                # Use a safer approach with explicit checks
                try:
                    df = get_salla_orders_for_project(request.project_id)
                    if df is None:
                        logger.warning(f"No Salla data returned for project {request.project_id}")
                        df = pd.DataFrame()  # Ensure we have an empty DataFrame not None
                    else:
                        logger.info(f"Using Salla DataFrame for project {request.project_id} with {len(df)} rows")
                except Exception as salla_err:
                    logger.error(f"Error fetching Salla data: {str(salla_err)}")
                    # Create an empty DataFrame instead of returning None
                    df = pd.DataFrame()
                
                # Run data analysis if we have data and it hasn't been analyzed yet
                if not df.empty and not project_analyzed:
                    try:
                        logger.info(f"Triggering data analysis for project {request.project_id}")
                        analyze_and_store_project_data(request.project_id, df, "Salla")
                        project_analyzed = True
                        logger.info("Data analysis completed successfully")
                    except Exception as analysis_err:
                        logger.error(f"Error during data analysis: {str(analysis_err)}")
                        # Continue with the request even if analysis fails
            except Exception as e:
                logger.error(f"Unhandled error in Salla integration: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                # Fall back to chat response if data loading fails
                response = get_openai_response(history, persona, industry, context)
                return {"type": "chat", "response": response}
        
        if df is None or df.empty:
            logger.warning("No data available for analysis, falling back to chat response")
            response = get_openai_response(history, persona, industry, context)
            return {"type": "chat", "response": response}
        
        # Initialize project metadata and data analysis if available
        project_metadata_dict = None
        data_analysis_dict = None
        data_source = "Salla" if request.project_id else "CSV"
        
        # Try to get project metadata if project_id is available
        if request.project_id:
            try:
                from supabase_helpers.project import get_project_metadata
                project_metadata_obj = get_project_metadata(request.project_id)
                if project_metadata_obj:
                    project_metadata_dict = project_metadata_obj.get("metadata", {})
                    logger.info(f"Loaded project metadata for analysis: {project_metadata_dict is not None}")
            except Exception as e:
                logger.warning(f"Error loading project metadata for analysis: {str(e)}")
        
        # Generate DataFrame analysis if not available from metadata
        if not project_metadata_dict:
            try:
                from utils.analyze_dataframe import analyze_dataframe
                data_analysis_dict = analyze_dataframe(df)
                logger.info(f"Generated data analysis with {len(data_analysis_dict.keys()) if data_analysis_dict else 0} metrics")
            except Exception as e:
                logger.warning(f"Error analyzing DataFrame: {str(e)}")
        
        # Generate intelligent analysis plan using the context-aware agent
        analysis_plan = generate_analysis_plan(
            messages=history,
            df=df,
            metadata=project_metadata_dict or data_analysis_dict,
            persona=persona,
            industry=industry,
            business_context=context,
            data_source=data_source
        )
        
        logger.info(f"Analysis plan generated - Type: {analysis_plan['result_type']}, Columns: {analysis_plan['columns']}")
        
        # Initialize smart DataFrame and execute the analysis
        smart_df = initialize_smart_df(df)
        
        try:
            # Use the generated pandas_prompt from the analysis plan
            result = ask_pandasai(smart_df, analysis_plan["pandas_prompt"])
            
            # TESTING: Bypass the narrative generator and return raw PandasAI results
            logger.info(f"DIRECT PANDASAI RESULT: {result}")
            
            # Set narrative to a simple message indicating we're in testing mode
            narrative = "TESTING MODE: Direct PandasAI results without narrative generation"
            
            # Save assistant message to Supabase if project_id is provided
            if request.project_id:
                try:
                    # We store the narrative as the content since it includes the analysis
                    save_message(
                        project_id=request.project_id,
                        role="assistant",
                        content=narrative,
                        intent="data_analysis"
                    )
                except Exception as e:
                    print(f"Error saving data analysis result: {str(e)}")
                    # Continue processing even if saving fails
            
            # Prepare the response based on the result type
            response_type = result.get("type", analysis_plan.get("result_type", "text"))
            
            # Create the base response
            response = {
                "type": response_type,
                "response": result.get("response", narrative),  # Use result response or narrative
                "narrative": narrative  # Always include the narrative for backward compatibility
            }
            
            # Add plot configuration if available
            if response_type == "plot" and "plot_config" in result:
                response["plot_config"] = result["plot_config"]
            # Add traditional metadata for backward compatibility
            else:
                response["metadata"] = {
                    "instruction": analysis_plan["pandas_prompt"],
                    "result_type": analysis_plan["result_type"],
                    "plot_type": analysis_plan.get("plot_type"),
                    "columns": analysis_plan["columns"]
                }
                
            return response
            
        except Exception as e:
            error_msg = f"Error during data analysis: {str(e)}"
            return {"type": "error", "response": error_msg}
