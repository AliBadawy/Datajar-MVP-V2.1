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

# Load environment variables
load_dotenv()

# Check if PandasAI is available - handle different versions
PANDASAI_AVAILABLE = False
PANDASAI_VERSION = None

# Set environment variable to prevent SSL warnings
os.environ["PYTHONHTTPSVERIFY"] = "0"

try:
    # Try importing from newer versions
    try:
        logger.info("Attempting to import PandasAI...")
        from pandasai import PandasAI
        from pandasai.llm import OpenAI
        import pandas as pd  # Ensure pandas is imported
        import matplotlib  # Ensure matplotlib is imported
        
        # Verify the imports worked
        assert pd is not None
        assert matplotlib is not None
        
        PANDASAI_AVAILABLE = True
        PANDASAI_VERSION = "new"
        logger.info("Successfully imported PandasAI (new version)")
    except ImportError as e:
        logger.warning(f"Failed to import new version of PandasAI: {e}")
        raise
        logger.info("Using newer version of PandasAI")
    except ImportError:
        # Try importing from older versions
        try:
            from pandasai.pandas_ai import PandasAI
            from pandasai.llm.openai import OpenAI
            PANDASAI_AVAILABLE = True
            PANDASAI_VERSION = "old"
            logger.info("Using older version of PandasAI")
        except ImportError:
            logger.warning("PandasAI not installed or import failed")
            PANDASAI_AVAILABLE = False
except Exception as e:
    logger.error(f"Error importing PandasAI: {str(e)}")
    PANDASAI_AVAILABLE = False

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
        PandasAI: Configured PandasAI instance or None if unavailable
    """
    if not PANDASAI_AVAILABLE:
        logger.warning("PandasAI is not available - cannot create instance")
        return None
        
    if not OPENAI_API_KEY:
        logger.warning("OpenAI API key is required for PandasAI")
        return None
    
    try:
        # Initialize the LLM (using OpenAI by default)
        if PANDASAI_VERSION == "new":
            # New version of PandasAI
            llm = OpenAI(api_token=OPENAI_API_KEY)
            return PandasAI(llm)
        else:
            # Old version of PandasAI
            llm = OpenAI(api_token=OPENAI_API_KEY)
            return PandasAI(llm)
    except Exception as e:
        logger.error(f"Error creating PandasAI instance: {str(e)}")
        return None

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
    
    # Check if PandasAI is available
    if not PANDASAI_AVAILABLE:
        logger.warning("PandasAI is not available for analysis")
        return {
            "response": "I'm sorry, but the PandasAI analysis engine is not available right now. Please check if the package is installed correctly.",
            "has_chart": False,
            "chart_data": None
        }
    
    try:
        # Get PandasAI instance
        pandas_ai = get_pandasai_instance()
        if pandas_ai is None:
            return {
                "response": "I couldn't initialize the PandasAI analysis engine. Please check your configuration and API keys.",
                "has_chart": False,
                "chart_data": None
            }
        
        # Prepare the enhanced query with dataframe context
        enhanced_query = f"""
        Analyze the following Salla orders data to answer this question: {query}
        
        The dataframe contains Salla e-commerce orders with these columns:
        {', '.join(df.columns.tolist())}
        
        There are {len(df)} orders in total.
        """
        
        # Run the analysis
        try:
            response = pandas_ai.run(df, enhanced_query)
            
            # If response is None or empty, provide a fallback
            if not response:
                logger.warning("PandasAI returned empty response")
                # Provide a simple analysis fallback
                response = f"I couldn't generate a detailed analysis, but I can tell you that there are {len(df)} orders in the dataset."
                
                # Add some basic statistics
                if 'total' in df.columns:
                    total_sum = df['total'].sum()
                    response += f" The total value of all orders is {total_sum}."
                
                if 'status' in df.columns:
                    status_counts = df['status'].value_counts().to_dict()
                    status_info = ", ".join([f"{count} orders with status '{status}'" for status, count in status_counts.items()])
                    response += f" Order statuses: {status_info}."
            
            # Check for charts in the response
            has_chart = False
            chart_data = None
            
            # Return the results
            return {
                "response": response,
                "has_chart": has_chart,
                "chart_data": chart_data
            }
        except Exception as run_error:
            logger.error(f"Error running PandasAI analysis: {str(run_error)}")
            
            # Provide a basic fallback analysis instead of failing
            fallback_response = f"I encountered an error while analyzing the data with PandasAI, but I can tell you that there are {len(df)} orders in the dataset."
            
            # Add some basic statistics
            if 'total' in df.columns:
                total_sum = df['total'].sum()
                fallback_response += f" The total value of all orders is {total_sum}."
            
            return {
                "response": fallback_response,
                "has_chart": False,
                "chart_data": None,
                "error": str(run_error)
            }
    
    except Exception as e:
        logger.error(f"Error in analyze_with_pandasai: {str(e)}")
        return {
            "response": f"Error analyzing data: {str(e)}",
            "has_chart": False,
            "chart_data": None
        }
