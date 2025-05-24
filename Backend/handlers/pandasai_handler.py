"""
PandasAI Handler

This module provides functions to interact with PandasAI for dataframe analysis.
It handles passing queries to PandasAI and retrieving responses.
"""

import logging
from typing import Dict, Any, Optional, List
import pandas as pd
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
openai_api_key = os.getenv('OPENAI_API_KEY')
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY environment variable not set")

def analyze_with_pandasai(df: pd.DataFrame, query: str, conversation_context: List[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Analyze a dataframe using PandasAI based on a natural language query.
    
    Args:
        df: The dataframe to analyze (Salla orders data)
        query: The user's question about the data
        conversation_context: Previous conversation messages (unused in this simple version)
        
    Returns:
        Dict with analysis results including response text and chart data
    """
    try:

        # Initialize the LLM
        llm = OpenAI(api_token=openai_api_key)
        
        # Create a SmartDataframe with the orders data
        smart_df = SmartDataframe(
            df,
            config={
                "llm": llm,
                "save_charts": False,
                "verbose": True,
                "enable_cache": False
            }
        )
        
        # Run the query
        response = smart_df.chat(query)
        
        # Format the response
        return {
            "response": str(response) if response else "No response generated",
            "has_chart": False,
            "chart_data": None
        }
        
    except Exception as e:
        logger.error(f"Error in analyze_with_pandasai: {str(e)}", exc_info=True)
        
        # Provide a fallback response with basic info
        fallback = f"I encountered an error: {str(e)}. "
        
        return {
            "response": fallback,
            "has_chart": False,
            "chart_data": None,
            "error": str(e)
        }
