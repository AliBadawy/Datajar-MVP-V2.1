"""
PandasAI Instruction Agent

This module contains functions to generate intelligent analysis plans for PandasAI
based on user input, DataFrame characteristics, and contextual information.
"""

import json
import logging
from typing import Dict, List, Any, Optional
import pandas as pd
from openai import OpenAI
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def get_client():
    """Get or initialize the OpenAI client"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY environment variable is not set")
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    return OpenAI(api_key=api_key)

def generate_analysis_plan(messages, df, metadata, persona, industry, business_context, data_source):
    """
    Uses GPT-4o to interpret user intent and generate an intelligent Pandas analysis plan.
    
    Args:
        messages (List[Dict]): History of conversation messages
        df (pd.DataFrame): The DataFrame to analyze
        metadata (Dict): Metadata about the DataFrame columns, types, etc.
        persona (str): The user's persona (e.g., "Marketer", "Analyst")
        industry (str): The industry context (e.g., "E-commerce")
        business_context (str): Custom business context
        data_source (str): Source of data (e.g., "Salla", "CSV")
        
    Returns:
        dict: {
            "result_type": "table" | "plot" | "value",
            "plot_type": "bar" | "line" | "pie" | None,
            "pandas_prompt": "Group sales by month and plot total revenue",
            "columns": ["month", "sales"]
        }
    """
    # Extract the latest user question
    user_prompt = messages[-1]["content"]
    
    # Create a sample of the data for context
    sample_data = df.head(3).to_dict(orient="records") if df is not None and not df.empty else []
    
    # Extract relevant column information
    column_info = {}
    if df is not None and not df.empty:
        for col in df.columns:
            column_info[col] = {
                "dtype": str(df[col].dtype),
                "missing": int(df[col].isna().sum()),
                "missing_percent": round(df[col].isna().sum() / len(df) * 100, 2),
                "sample_values": df[col].dropna().sample(min(3, len(df[col].dropna()))).tolist(),
            }
    
    # Build a comprehensive system prompt with Saudi/Salla specific context
    system_content = f"""
You are an advanced AI assistant helping analyze datasets from Salla Stores operating in Saudi Arabia.
You excel at understanding:
- Saudi retail metrics and KPIs
- Arabic e-commerce terminology and practices
- Business analytics relevant to marketers, analysts, and operators
- Salla store structure, order processing, and typical column naming conventions

The user is a {persona} working in the {industry} industry.
Business Context: {business_context}

The data comes from {data_source}.

Here's sample data:
{json.dumps(sample_data, indent=2)}

Here's information about the dataset columns:
{json.dumps(column_info, indent=2)}

Additional dataset metadata:
{json.dumps(metadata, indent=2) if metadata else "No additional metadata available"}

Given this context and the user's question, return ONLY a JSON object (no explanation) with:
- "result_type": "table", "plot", or "value"
- "plot_type": (if result_type is "plot") "bar", "line", "pie", "scatter", etc.
- "columns": list of column names relevant to the analysis
- "pandas_prompt": clear instruction to pass to PandasAI that will answer the user's question

Guidelines for different result types:
- Use "table" for detailed data exploration or when multiple columns need to be shown
- Use "plot" for trend analysis, comparisons, or distributions
- Use "value" for single metrics, counts, averages, or simple answers

For Saudi/Salla context:
- Consider that dates may need to follow Hijri calendar conventions
- Currency values are typically in SAR (Saudi Riyal)
- For e-commerce metrics, consider: conversion rate, AOV (Average Order Value), CLV (Customer Lifetime Value)
- Popular Salla KPIs: sales by region, order status distribution, payment method preferences

ONLY RETURN VALID JSON. No introduction or explanation text.
"""

    # Create messages for the API call
    api_messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_prompt}
    ]
    
    # Log the request
    logger.info(f"Generating analysis plan for: '{user_prompt[:50]}...'")
    
    try:
        # Call GPT-4o for intelligent analysis planning
        client = get_client()
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=api_messages,
            response_format={"type": "json_object"}  # Force JSON response
        )
        
        # Extract and parse the JSON
        response_content = response.choices[0].message.content.strip()
        analysis_plan = json.loads(response_content)
        
        # Log the generated plan
        logger.info(f"Generated analysis plan: {analysis_plan['result_type']} with prompt: {analysis_plan['pandas_prompt'][:50]}...")
        
        return analysis_plan
    
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {str(e)}")
        logger.error(f"Raw response: {response.choices[0].message.content}")
        # Return a fallback plan
        return {
            "result_type": "table",
            "plot_type": None,
            "columns": list(df.columns) if df is not None and not df.empty else [],
            "pandas_prompt": f"Analyze the data to answer: {user_prompt}"
        }
    
    except Exception as e:
        logger.error(f"Error generating analysis plan: {str(e)}")
        # Return a fallback plan
        return {
            "result_type": "table",
            "plot_type": None,
            "columns": list(df.columns) if df is not None and not df.empty else [],
            "pandas_prompt": f"Analyze the data to answer: {user_prompt}"
        }
