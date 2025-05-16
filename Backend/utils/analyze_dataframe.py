"""
DataFrame Analysis Utility

This module contains functions to analyze and extract metadata from pandas DataFrames,
providing comprehensive information for data exploration.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional

def analyze_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyze a pandas DataFrame and extract comprehensive metadata.
    
    Args:
        df: Pandas DataFrame to analyze
    
    Returns:
        Dictionary containing metadata about the DataFrame
    """
    if df is None or df.empty:
        return {
            "message": "No data to analyze",
            "data_types": {},
            "head_rows": [],
            "categorical_data": {},
            "missing_data": {},
            "numerical_stats": {},
            "date_parts": {},
            "inconsistent_columns": []
        }
    
    # Extract basic metadata
    total_rows = df.shape[0]
    total_columns = df.shape[1]
    
    # Get data types for each column
    data_types = {}
    for col in df.columns:
        data_types[col] = str(df[col].dtype)
    
    # Get sample rows (5% or up to 5 rows if small dataset)
    sample_size = min(int(total_rows * 0.05) + 1, 5) if total_rows > 0 else 0
    head_rows = df.head(sample_size).to_dict(orient='records')
    
    # Extract categorical data
    categorical_data = {}
    for col in df.columns:
        if pd.api.types.is_categorical_dtype(df[col]) or pd.api.types.is_object_dtype(df[col]):
            # Get top 5 values and their counts
            value_counts = df[col].value_counts().head(5).to_dict()
            categorical_data[col] = [{"value": str(k), "count": int(v)} for k, v in value_counts.items()]
    
    # Calculate missing data
    missing_data = {}
    for col in df.columns:
        null_count = int(df[col].isna().sum())
        null_percent = round((null_count / total_rows) * 100, 2) if total_rows > 0 else 0
        missing_data[col] = {"count": null_count, "percent": null_percent}
    
    # Calculate numerical statistics
    numerical_stats = {}
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            try:
                col_stats = {
                    "min": float(df[col].min()) if not pd.isna(df[col].min()) else None,
                    "max": float(df[col].max()) if not pd.isna(df[col].max()) else None,
                    "mean": float(df[col].mean()) if not pd.isna(df[col].mean()) else None,
                    "median": float(df[col].median()) if not pd.isna(df[col].median()) else None,
                    "std": float(df[col].std()) if not pd.isna(df[col].std()) else None
                }
                
                # Find min/max row indices
                if not df[col].isna().all():
                    min_idx = int(df[col].idxmin()) if not pd.isna(df[col].min()) else None
                    max_idx = int(df[col].idxmax()) if not pd.isna(df[col].max()) else None
                    col_stats["min_row_idx"] = min_idx
                    col_stats["max_row_idx"] = max_idx
                
                numerical_stats[col] = col_stats
            except Exception as e:
                # Skip columns that can't be analyzed numerically
                pass
    
    # Extract date parts for datetime columns
    date_parts = {}
    for col in df.columns:
        # Try to convert to datetime
        try:
            if pd.api.types.is_datetime64_dtype(df[col]) or pd.api.types.is_datetime64_dtype(pd.to_datetime(df[col], errors='coerce')):
                dt_series = pd.to_datetime(df[col], errors='coerce')
                if dt_series.notna().sum() > 0:  # Only if we have valid dates
                    date_parts[col] = {
                        "has_year": not dt_series.dt.year.isna().all(),
                        "has_month": not dt_series.dt.month.isna().all(),
                        "has_day": not dt_series.dt.day.isna().all(),
                        "has_time": not dt_series.dt.hour.isna().all(),
                        "min_date": dt_series.min().strftime('%Y-%m-%d') if not pd.isna(dt_series.min()) else None,
                        "max_date": dt_series.max().strftime('%Y-%m-%d') if not pd.isna(dt_series.max()) else None
                    }
        except:
            # Skip if conversion fails
            pass
    
    # Identify inconsistent columns (mixed types)
    inconsistent_columns = []
    for col in df.columns:
        # Check if column has mixed types
        if df[col].apply(type).nunique() > 1:
            type_counts = df[col].apply(lambda x: type(x).__name__).value_counts().to_dict()
            inconsistent_columns.append({
                "column": col,
                "types": [{"type": k, "count": int(v)} for k, v in type_counts.items()]
            })
    
    return {
        "data_types": data_types,
        "head_rows": head_rows,
        "categorical_data": categorical_data,
        "missing_data": missing_data,
        "numerical_stats": numerical_stats,
        "date_parts": date_parts,
        "inconsistent_columns": inconsistent_columns
    }
