from fastapi import APIRouter, HTTPException
from models.schemas import AnalyzeRequest
from handlers.openai_handler import (
    get_openai_response,
    classify_user_prompt,
    wrap_pandasai_result_with_gpt,
    generate_pandasai_instruction
)
from handlers.pandasai_handler import initialize_smart_df, ask_pandasai
from handlers.dataframe_handler import analyze_and_store_project_data
from supabase_helpers.message import save_message, get_messages_by_project
from supabase_helpers.project import get_project_by_id
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
        
        # Create static analysis data
        column_details = {
            "order_id": { "type": "string", "missing": 0 },
            "customer_name": { "type": "string", "missing": 3 },
            "amount": { "type": "numeric", "missing": 0 },
            "date": { "type": "datetime", "missing": 0 },
            "status": { "type": "string", "missing": 0 },
        }
        
        # Create a response object for the frontend
        response_data = {
            "status": "success",
            "project_id": project_id,
            "summary": {
                "sources": ["Salla"],
                "total_rows": 120
            },
            "metadata": {
                "analyzed_at": "2025-05-17T12:00:00Z",
                "data_sources": ["Salla"],
                "basic_stats": {
                    "total_records": 120,
                    "columns_analyzed": len(column_details),
                    "missing_data_percentage": 2.5,
                },
                "column_details": column_details
            }
        }
        
        # Data for saving to Supabase in the new project_metadata table
        # Format this according to what save_project_metadata expects
        supabase_data = {
            "metadata": response_data,  # Store the complete analysis result
            "data_sources": ["Salla"]
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
    intent = classify_user_prompt(user_message)
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
    
    # 1. Determine if it's a chat message or a data analysis query
    last_message = request.messages[-1]
    intent = classify_user_prompt(last_message["content"])
    
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
    if intent == "chat" or not request.dataframe:
        # Pass all context to get more personalized responses
        response = get_openai_response(history, persona, industry, context)
        
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
                df = get_salla_orders_for_project(request.project_id)
                logger.info(f"Using Salla DataFrame for project {request.project_id} with {len(df) if df is not None else 0} rows")
                
                # Run data analysis if we have data and it hasn't been analyzed yet
                if df is not None and not df.empty and not project_analyzed:
                    try:
                        logger.info(f"Triggering data analysis for project {request.project_id}")
                        analyze_and_store_project_data(request.project_id, df, "Salla")
                        project_analyzed = True
                        logger.info("Data analysis completed successfully")
                    except Exception as e:
                        logger.error(f"Error during data analysis: {str(e)}")
                        # Continue with the request even if analysis fails
            except Exception as e:
                logger.error(f"Error loading Salla data: {str(e)}")
                # Fall back to chat response if data loading fails
                response = get_openai_response(history, persona, industry, context)
                return {"type": "chat", "response": response}
        
        if df is None or df.empty:
            logger.warning("No data available for analysis, falling back to chat response")
            response = get_openai_response(history, persona, industry, context)
            return {"type": "chat", "response": response}
        
        # Initialize smart DataFrame and generate instruction
        smart_df = initialize_smart_df(df)
        instruction = generate_pandasai_instruction(history, df)
        
        try:
            result = ask_pandasai(smart_df, instruction)
            
            # Generate a natural language narrative using GPT with enhanced context
            narrative = wrap_pandasai_result_with_gpt(
                user_prompt=last_message["content"],
                pandas_instruction=instruction,
                pandas_result=result["value"],
                df=df,
                persona=persona,
                industry=industry,
                business_context=context,
                chat_history=history
            )
            
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
            
            return {
                "type": "data_analysis",
                "pandas_result": result["value"],
                "narrative": narrative
            }
            
        except Exception as e:
            error_msg = f"Error during data analysis: {str(e)}"
            return {"type": "error", "response": error_msg}
