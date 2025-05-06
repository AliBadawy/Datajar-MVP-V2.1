import pandas as pd
from pandasai import SmartDataframe
from pandasai.llm import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI LLM for PandasAI
def get_pandasai_llm():
    """
    Initialize and return the OpenAI LLM for PandasAI
    """
    return OpenAI(api_token=os.getenv("OPENAI_API_KEY"))

def initialize_smart_df(df):
    """
    Initialize a SmartDataframe with the given pandas DataFrame
    
    Args:
        df (pandas.DataFrame): The DataFrame to transform into a SmartDataframe
        
    Returns:
        SmartDataframe: The PandasAI SmartDataframe
    """
    llm = get_pandasai_llm()
    return SmartDataframe(df, config={"llm": llm})

def ask_pandasai(smart_df, instruction):
    """
    Ask a question to PandasAI
    
    Args:
        smart_df (SmartDataframe): The PandasAI SmartDataframe
        instruction (str): The instruction/question for PandasAI
        
    Returns:
        dict: The result from PandasAI with keys 'value' and 'type'
    """
    try:
        # Execute the instruction on the SmartDataframe
        result = smart_df.chat(instruction)
        
        # Determine if the result is a DataFrame, plot, or other
        if isinstance(result, pd.DataFrame):
            result_type = "dataframe"
            # Convert DataFrame to dict for JSON serialization
            result_value = result.to_dict(orient="records")
        elif str(type(result)).find("Figure") > -1:  # Matplotlib figure
            result_type = "plot"
            result_value = "Plot was generated"
        else:
            result_type = "text"
            result_value = str(result)
            
        return {"value": result_value, "type": result_type}
    
    except Exception as e:
        return {"value": f"Error in PandasAI processing: {str(e)}", "type": "error"}
