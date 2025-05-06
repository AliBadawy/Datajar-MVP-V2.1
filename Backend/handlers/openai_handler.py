from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def classify_user_prompt(prompt: str) -> str:
    """
    Classifies a user prompt as either 'chat' or 'data_analysis'.
    
    Args:
        prompt (str): The user's message to classify
        
    Returns:
        str: 'chat' or 'data_analysis'
    """
    classification_prompt = [
        {"role": "system", "content": "Classify the following user prompt as either 'chat' or 'data_analysis'. Only reply with one word: chat or data_analysis."},
        {"role": "user", "content": prompt}
    ]

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=classification_prompt
    )
    
    intent = response.choices[0].message.content.strip().lower()
    
    # Ensure the response is one of the expected values
    if intent not in ["chat", "data_analysis"]:
        # Default to chat if the response doesn't match expected values
        intent = "chat"
        
    return intent
