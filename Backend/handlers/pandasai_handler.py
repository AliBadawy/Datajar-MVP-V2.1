"""
PandasAI Handler

This module provides functions to interact with PandasAI for dataframe analysis.
It handles passing queries to PandasAI and retrieving responses.
"""

import logging
from typing import Dict, Any, Optional, List
import pandas as pd
from pandasai import PandasAI
from pandasai.llm import OpenAI
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Check if the API key is available
if not OPENAI_API_KEY:
    logger.warning("OPENAI_API_KEY not found in environment variables. PandasAI will not work.")

# Initialize PandasAI with OpenAI LLM
def get_pandasai_instance():
    """
    Get a configured PandasAI instance.
    
    Returns:
        PandasAI: Configured PandasAI instance
    """
    if not OPENAI_API_KEY:
        raise ValueError("OpenAI API key is required for PandasAI")
    
    # Initialize the LLM (using OpenAI by default)
    llm = OpenAI(api_token=OPENAI_API_KEY)
    
    # Initialize PandasAI with the LLM
    return PandasAI(llm)

def analyze_with_pandasai(df: pd.DataFrame, query: str, conversation_context: List[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Analyze a dataframe using PandasAI based on a natural language query.
    
    Args:
        df (pd.DataFrame): The dataframe to analyze
        query (str): Natural language query to analyze the dataframe
        conversation_context (List[Dict]): Optional previous conversation for context
        
    Returns:
        Dict[str, Any]: Analysis result with response and any generated visualizations
    """
    if df is None or df.empty:
        return {
            "response": "No data available for analysis. Please make sure you have Salla orders data for this project.",
            "has_chart": False,
            "chart_data": None
        }
    
    try:
        # Get PandasAI instance
        pandas_ai = get_pandasai_instance()
        
        # Prepare the enhanced query with dataframe context
        enhanced_query = f"""
        Analyze the following Salla orders data to answer this question: {query}
        
        The dataframe contains Salla e-commerce orders with these columns:
        {', '.join(df.columns.tolist())}
        
        There are {len(df)} orders in total.
        """
        
        # Run the analysis
        response = pandas_ai.run(df, enhanced_query)
        
        # Check for charts in the response
        has_chart = False
        chart_data = None
        
        # Return the results
        return {
            "response": response,
            "has_chart": has_chart,
            "chart_data": chart_data
        }
    
    except Exception as e:
        logger.error(f"Error analyzing with PandasAI: {str(e)}")
        return {
            "response": f"Error analyzing data: {str(e)}",
            "has_chart": False,
            "chart_data": None
        }
