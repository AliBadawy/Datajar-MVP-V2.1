import logging
from typing import Dict, List, Optional, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def simplified_prompt_handler(prompt: str) -> str:
    """
    A simplified function that returns 'chat' for all prompts.
    
    Args:
        prompt (str): The user's message
        
    Returns:
        str: Always returns 'chat'
    """
    # Log the incoming message
    logger.info(f"Received message: {prompt[:50]}...")
    
    # Always classify as chat
    return "chat"


def get_simple_response(message: str) -> str:
    """
    Returns a simple acknowledgment of the message.
    
    Args:
        message (str): The user's message
        
    Returns:
        str: A simple acknowledgment response
    """
    return f"Message received: '{message[:30]}...'"
