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
import pandas as pd
from typing import Optional

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
        response = get_openai_response(request.messages)
        
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

        instruction = generate_pandasai_instruction(request.messages, df)
        result = ask_pandasai(smart_df, instruction)

        narrative = wrap_pandasai_result_with_gpt(
            result = str(result),
            query = request.messages[-1]["content"],
            industry = request.industry,
            business_context = request.business_context,
            persona = request.persona
        )
        
        # Save assistant response to Supabase if project_id is provided
        if request.project_id:
            try:
                save_message(
                    project_id=request.project_id,
                    role="assistant",
                    content=narrative,
                    intent="data_analysis"
                )
            except Exception as e:
                print(f"Error saving assistant message: {str(e)}")
                # Continue processing even if saving fails
        
        return {
            "type": "data_analysis",
            "pandas_result": result,
            "narrative": narrative
        }
