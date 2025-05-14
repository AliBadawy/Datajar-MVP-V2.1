"""
DataFrame Handler

This module provides handlers for DataFrame operations, 
including analyzing and extracting metadata from uploaded data.
"""

import pandas as pd
from typing import Dict, Any, Optional, Union
import traceback
import logging
from utils.analyze_dataframes import analyze_project_data
from supabase_helpers.project import update_project_metadata

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_and_store_project_data(
    project_id: int, 
    df: Optional[pd.DataFrame] = None, 
    source: str = "CSV"
) -> Dict[str, Any]:
    """
    Analyze project data and store the metadata in Supabase.
    
    Args:
        project_id: The ID of the project to analyze
        df: Optional DataFrame to analyze (will be loaded from project sources if None)
        source: The source of the DataFrame (e.g., "CSV", "Salla")
        
    Returns:
        Dictionary containing the analysis metadata
    """
    try:
        logger.info(f"Starting analysis for project {project_id}")
        
        # Analyze the data
        metadata = analyze_project_data(project_id, df, source)
        
        # Store the metadata in Supabase
        if metadata and metadata.get("dataframes"):
            logger.info(f"Updating project {project_id} with metadata")
            success = update_project_metadata(project_id, {"data_analysis": metadata})
            if not success:
                logger.error(f"Failed to update project metadata for project {project_id}")
        else:
            logger.info(f"No data to analyze for project {project_id}")
            
        return metadata
    
    except Exception as e:
        error_msg = f"Error analyzing project data: {str(e)}"
        stack_trace = traceback.format_exc()
        logger.error(f"{error_msg}\n{stack_trace}")
        
        # Return error information
        return {
            "project_id": project_id,
            "error": error_msg,
            "dataframes": []
        }
