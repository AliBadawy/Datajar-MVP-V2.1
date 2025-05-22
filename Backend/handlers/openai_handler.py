from openai import OpenAI
import os
from dotenv import load_dotenv
import json
import pandas as pd
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize OpenAI client with lazy loading
_client = None

def get_client():
    """Get or initialize the OpenAI client"""
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("OPENAI_API_KEY environment variable is not set")
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        _client = OpenAI(api_key=api_key)
    return _client

from typing import Optional
from utils.analyze_dataframe import analyze_dataframe

def classify_user_prompt(prompt: str, df: Optional[pd.DataFrame] = None) -> str:
    """
    Classifies a user prompt as either 'chat' or 'data_analysis' with context awareness.
    
    Args:
        prompt (str): The user's message to classify
        df (Optional[pd.DataFrame]): DataFrame with data context, if available
        
    Returns:
        str: 'chat' or 'data_analysis'
    """
    try:
        # Enhanced data context preparation
        data_context = {}
        
        if df is not None and not df.empty:
            # Include actual column names and sample data for better context
            data_context["columns"] = list(df.columns)
            data_context["row_count"] = len(df)
            data_context["column_count"] = len(df.columns)
            
            # Only include sample data if we have a reasonable number of rows
            if len(df) > 0:
                # Get the first few rows as a sample (convert to dict for serialization)
                try:
                    data_context["sample_data"] = df.head(3).to_dict(orient="records")
                except:
                    # Fallback if to_dict fails
                    data_context["sample_data"] = "[Sample data available but could not be converted]"
        
        # Add full data analysis if the dataframe is not too large
        if df is not None and not df.empty and len(df) < 10000:
            try:
                data_context["analysis"] = analyze_dataframe(df)
            except Exception as e:
                logger.warning(f"Error analyzing dataframe: {str(e)}")
                data_context["analysis_error"] = str(e)
        
        # Convert to string format for the prompt
        if data_context:
            metadata_str = json.dumps(data_context, indent=2)
        else:
            metadata_str = "No dataset provided"
            
        # Common keywords and phrases that indicate data analysis intent
        # These are just examples to guide the model, not strict rules
        data_keywords = [
            "how many", "count", "total", "average", "mean", "median", "sum", 
            "maximum", "minimum", "chart", "graph", "plot", "visualization",
            "breakdown", "compare", "comparison", "trend", "analyze", "analysis",
            "orders", "sales", "revenue", "products", "customers", "show me",
            "list", "display", "highest", "lowest", "top", "bottom", "distribution",
            "calculate", "percentage", "ratio", "proportion", "frequency",
            "summarize", "aggregate", "group by", "filter", "where", "when",
            "most popular", "least popular", "best selling", "worst selling",
            "growth", "decline", "increase", "decrease", "change", "difference"
        ]

        # Create a context-aware classification prompt with better instructions
        messages = [
            {"role": "system", "content": (
                "You are an advanced intent classification system specializing in data analytics and business intelligence.\n\n"
                "YOUR TASK:\n"
                "Analyze the user's query and classify it as either 'data_analysis' or 'chat'.\n\n"
                "CLASSIFICATION GUIDELINES:\n"
                "1. 'data_analysis': Queries that seek insights, statistics, visualizations, or information that can be derived from data.\n"
                "2. 'chat': General conversation, small talk, or questions not answerable from the available data.\n\n"
                
                "IMPORTANT: These are flexible guidelines, not rigid rules. Use your full intelligence to understand the user's true intent.\n\n"
                
                "Common indicators of data analysis intent include (but are NOT limited to):\n"
                f"{', '.join(data_keywords[:20])}\n"
                f"{', '.join(data_keywords[20:40])}\n"
                f"{', '.join(data_keywords[40:])}\n\n"
                
                "ALWAYS ERR ON THE SIDE OF DATA ANALYSIS when the query is ambiguous or could potentially be answered with data.\n\n"
                
                "AVAILABLE DATA CONTEXT:\n"
                f"{metadata_str}\n\n"
                
                "YOU MUST RESPOND WITH EXACTLY ONE WORD: either 'chat' or 'data_analysis'\n"
                "Do not include any explanation or additional text."
            )},
            {"role": "user", "content": prompt}
        ]

        # Use GPT-4o for better classification accuracy
        response = get_client().chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.0  # Zero temperature for maximum consistency
        )
        
        intent = response.choices[0].message.content.strip().lower()
        
        # Ensure the response is one of the expected values
        if intent not in ["chat", "data_analysis"]:
            logger.warning(f"Unexpected classification response: {intent}. Defaulting to 'chat'.")
            intent = "chat"
            
        logger.info(f"Classified prompt as: {intent}")
        return intent
        
    except Exception as e:
        logger.error(f"[classify_user_prompt] Error: {e}")
        return "chat"  # Default to chat on errors

def get_openai_response(messages, persona="Data Analyst", industry="E-Commerce", business_context="", project_metadata=None, data_analysis=None, df=None):
    """
    Gets a response from OpenAI's chat completion API with rich context including project metadata and data analysis
    
    Args:
        messages (List[Dict[str, str]]): List of message objects
        persona (str): The persona of the AI assistant
        industry (str): The industry context for responses
        business_context (str): Additional business context
        project_metadata (Dict, optional): Project metadata from the metadata table
        data_analysis (Dict, optional): Analysis of the DataFrame if available
        df (pd.DataFrame, optional): The actual DataFrame if available
        
    Returns:
        str: The AI response text personalized to the context
    """
    # Build a comprehensive system prompt with all available context
    data_context = ""
    
    # Add data source information if available
    if project_metadata:
        try:
            sources = project_metadata.get("data_sources", [])
            if sources:
                data_context += f"\nData sources available: {', '.join(sources)}"
        except Exception as e:
            logger.warning(f"Error processing project metadata: {str(e)}")
    
    # Add DataFrame information if available
    if df is not None and not df.empty:
        try:
            data_context += f"\n\nDataFrame information:\n- {len(df)} rows\n- {len(df.columns)} columns: {', '.join(df.columns.tolist())}"
            # Add basic stats about the data
            if data_analysis:
                if 'basic_stats' in data_analysis:
                    stats = data_analysis['basic_stats']
                    data_context += f"\n- Records analyzed: {stats.get('total_records', 'unknown')}"
                    data_context += f"\n- Missing data: {stats.get('missing_data_percentage', 0)}%"
                
                # Add column type information
                if 'data_types' in data_analysis:
                    data_context += "\n\nColumn types:"
                    for col, dtype in data_analysis['data_types'].items():
                        data_context += f"\n- {col}: {dtype}"
        except Exception as e:
            logger.warning(f"Error adding DataFrame context: {str(e)}")
    
    # Create a comprehensive personalized system prompt
    system_content = f"""You are a helpful {persona} assistant specialized in the {industry} industry.

    {business_context if business_context else ''}
    
    {data_context}

    Provide clear, concise, and actionable insights based on your expertise and the available data.
    When referring to data, be specific about the source and limitations of the analysis.
    """
    
    logger.info(f"Created system prompt with data context: {len(data_context) > 0}")
    
    # Add or replace the system message
    has_system = False
    for msg in messages:
        if msg.get("role") == "system":
            msg["content"] = system_content
            has_system = True
            break
            
    if not has_system:
        messages = [{"role": "system", "content": system_content}] + messages
    
    # Use GPT-4o for a more capable model that can handle the complex context
    try:
        response = get_client().chat.completions.create(
            model="gpt-4o",  # Upgraded to GPT-4o for better context handling
            messages=messages
        )
        
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error calling GPT-4o: {str(e)}. Falling back to GPT-3.5-turbo.")
        # Fallback to GPT-3.5-turbo if GPT-4o fails
        response = get_client().chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        
        return response.choices[0].message.content

def generate_pandasai_instruction(messages, df):
    """
    Generates an instruction for PandasAI based on user messages and dataframe
    
    Args:
        messages (List[Dict[str, str]]): List of message objects
        df (pandas.DataFrame): The dataframe to analyze
        
    Returns:
        str: A clear instruction for PandasAI
    """
    # Get the most recent user message
    user_message = messages[-1]["content"]
    
    # Get dataframe info
    columns = list(df.columns)
    sample_data = df.head(3).to_dict(orient="records")
    
    # Create a prompt for OpenAI to generate a clear pandas instruction
    system_prompt = """
    You are a data analysis expert who translates user questions into clear instructions for pandas.
    Based on the user's question and the dataframe information provided, generate a CONCISE, SPECIFIC 
    instruction that explains exactly what to analyze or calculate.
    Do NOT write code. Just provide a clear analytical instruction.
    """
    
    user_content = f"""
    User question: {user_message}
    
    DataFrame columns: {columns}
    
    Sample data: {json.dumps(sample_data)}
    
    Generate a clear instruction for PandasAI:
    """
    
    messages_for_generation = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ]
    
    response = get_client().chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages_for_generation
    )
    
    return response.choices[0].message.content.strip()

def wrap_pandasai_result_with_gpt(user_prompt, pandas_instruction, pandas_result,
                                df, persona="Data Analyst", industry="E-Commerce", 
                                business_context="", chat_history=None):
    """
    Generates a narrative around the PandasAI result using GPT
    
    Args:
        user_prompt (str): The original user question
        pandas_instruction (str): The instruction generated for PandasAI
        pandas_result (str): The result returned by PandasAI
        df (pandas.DataFrame): The dataframe that was analyzed
        persona (str): The persona to use for the narrative
        industry (str): The industry context
        business_context (str): Additional business context
        chat_history (List[Dict]): Previous messages for context
        
    Returns:
        str: A narrative explaining the results
    """
    # Get dataframe info
    columns = list(df.columns)
    df_summary = f"DataFrame with {df.shape[0]} rows and columns: {', '.join(columns)}"
    
    # Create a system prompt based on persona and industry
    system_prompt = f"""
    You are an experienced {persona} specializing in {industry}. 
    
    Your task is to provide a clear, concise explanation of data analysis results. Use the following approach:
    1. Analyze the result and provide the key insights
    2. Explain what these results mean in business terms
    3. If appropriate, suggest any follow-up analysis or actions
    
    Write in a professional, clear tone and avoid unnecessary jargon. Keep answers concise.
    """
    
    # Build user content with all context
    user_content = f"""
    Original user question: {user_prompt}
    
    Instruction given to pandas: {pandas_instruction}
    
    Analysis result: {pandas_result}
    
    Dataset information: {df_summary}
    
    Business context: {business_context if business_context else "Not provided"}
    
    Based on this analysis, provide a clear, insightful explanation:
    """
    
    messages_for_narrative = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ]
    
    # Add chat history for context if provided
    if chat_history and len(chat_history) > 1:
        # Insert chat history between system and user messages, but limit to last 5 exchanges
        relevant_history = chat_history[:-1][-5:]  # Exclude current message, limit to 5
        messages_for_narrative = [messages_for_narrative[0]] + relevant_history + [messages_for_narrative[1]]
    
    response = get_client().chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages_for_narrative
    )
    
    return response.choices[0].message.content.strip()
