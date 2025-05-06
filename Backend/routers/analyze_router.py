from fastapi import APIRouter
from models.schemas import AnalyzeRequest
from handlers.openai_handler import classify_user_prompt

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
