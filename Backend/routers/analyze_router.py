from fastapi import APIRouter, HTTPException
from models.schemas import AnalyzeRequest
from handlers.openai_handler import (
    get_openai_response,
    classify_user_prompt,
    wrap_pandasai_result_with_gpt,
    generate_pandasai_instruction
)
from handlers.pandasai_handler import initialize_smart_df, ask_pandasai
from supabase_helpers.message import save_message, get_messages_by_project
from supabase_helpers.project import get_project_by_id
import pandas as pd
from typing import Optional, List, Dict, Any

router = APIRouter()

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
        df = pd.DataFrame(request.dataframe)
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
