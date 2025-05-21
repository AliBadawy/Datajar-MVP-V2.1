import pandas as pd
# pandasai_handler.py
import os
import glob
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv
from pandasai import SmartDataframe
from pandasai.llm import OpenAI

# Load env vars
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Create chart output directory
IMG_DIR = "imgs"
os.makedirs(IMG_DIR, exist_ok=True)

# Initialize OpenAI LLM for PandasAI
llm = OpenAI(api_token=OPENAI_API_KEY)

# Clean up old charts
def _rotate_old_charts(max_charts=30):
    files = sorted(glob.glob(os.path.join(IMG_DIR, "*.png")), key=os.path.getctime)
    while len(files) > max_charts:
        os.remove(files[0])
        files = files[1:]

# Get the latest chart created
def get_latest_chart(since_timestamp=None):
    chart_files = glob.glob(os.path.join(IMG_DIR, "*.png"))
    if not chart_files:
        return None
    latest = max(chart_files, key=os.path.getctime)
    if since_timestamp and os.path.getctime(latest) < since_timestamp:
        return None
    return latest

# Init SmartDataframe
def initialize_smart_df(df):
    return SmartDataframe(df, config={
        "llm": llm,
        "save_charts": True,
        "save_charts_path": IMG_DIR,
        "verbose": True
    })

def ask_pandasai(sdf, instruction):
    """
    Execute a PandasAI instruction and return a JSON-formatted response
    including inferred plot configuration, text summary, or data table.

    Returns:
        dict: {
            "type": "plot" | "text" | "dataframe" | "error",
            "response": str | list | dict,
            "plot_config": dict (optional)
        }
    """
    try:
        # Run PandasAI
        result = sdf.chat(instruction)

        # CASE: If result is a DataFrame, determine plotting possibility
        if isinstance(result, pd.DataFrame):
            # Heuristic: use first 2 numeric columns (or 1 string + 1 numeric)
            numeric_cols = result.select_dtypes(include=["number"]).columns.tolist()
            string_cols = result.select_dtypes(include=["object", "category"]).columns.tolist()
            
            x_axis = string_cols[0] if string_cols else numeric_cols[0]
            y_axis = numeric_cols[0] if string_cols else numeric_cols[1] if len(numeric_cols) > 1 else numeric_cols[0]

            return {
                "type": "plot",
                "response": result.to_dict(orient="records"),
                "plot_config": {
                    "x_field": x_axis,
                    "y_field": y_axis,
                    "chart_type": "bar"  # or "line", "area", etc., update with logic if needed
                }
            }

        # CASE: If result is a simple textual summary
        elif isinstance(result, str):
            return {
                "type": "text",
                "response": result
            }

        # CASE: If result is something else (fallback)
        elif hasattr(result, "to_dict"):
            return {
                "type": "dataframe",
                "response": result.to_dict(orient="records")
            }

        # Unknown result
        return {
            "type": "text",
            "response": str(result)
        }

    except Exception as e:
        return {
            "type": "error",
            "response": str(e)
        }
