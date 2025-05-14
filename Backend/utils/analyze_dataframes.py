"""
DataFrame Analysis Utility

This module contains functions to analyze and extract metadata from DataFrames,
providing comprehensive profiling information that can be used to enhance
AI-powered data analysis capabilities.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Any, Optional, Union
import json

def analyze_dataframes(dataframes: List[Tuple[pd.DataFrame, str]]) -> List[Dict]:
    """
    Analyze a list of DataFrames and extract comprehensive metadata.
    
    Args:
        dataframes: List of tuples, each containing a DataFrame and its source identifier
                   (e.g., [df1, "CSV"], [df2, "Salla"])
    
    Returns:
        List of metadata dictionaries, one for each DataFrame
    """
    all_metadata = []
    
    # Global metadata
    global_metadata = {
        "dataframe_count": len(dataframes)
    }
    
    for df, source in dataframes:
        # Skip empty DataFrames
        if df is None or df.empty:
            continue
            
        df_metadata = {
            "source": source,
            "total_rows": df.shape[0],
            "total_columns": df.shape[1],
            "columns": [],
            "sample": [],
            "file_size_mb": df.memory_usage(deep=True).sum() / (1024 * 1024)
        }
        
        # Process each column
        for col in df.columns:
            series = df[col]
            original_dtype = str(series.dtype)
            
            # Detect data type with pandas
            coerced_dtype = pd.api.types.infer_dtype(series, skipna=True)
            
            # Initialize column metadata
            col_meta = {
                "name": col,
                "original_dtype": original_dtype,
                "dtype_detected": coerced_dtype,
                "null_count": int(series.isnull().sum()),
                "empty_string_count": int((series.astype(str).str.strip() == "").sum()) if series.dtype == object else 0,
                "sample_values": series.dropna().head(5).tolist(),
                "has_mixed_types": series.apply(type).nunique() > 1,
                "unique_count": int(series.nunique()),
                "is_categorical": False,
                "categories": [],
                "mixed_types": [],
                "datetime_parts": {},
                "numerical_stats": {},
            }
            
            # Check for mixed types
            if col_meta["has_mixed_types"]:
                # Get the different types in the column
                type_counts = series.apply(lambda x: type(x).__name__).value_counts().to_dict()
                col_meta["mixed_types"] = [{"type": k, "count": v} for k, v in type_counts.items()]
            
            # Check for categorical data (low cardinality columns)
            if coerced_dtype in ["string", "boolean", "categorical"] or series.dtype == object:
                unique_values = series.value_counts()
                if len(unique_values) <= 20:
                    col_meta["is_categorical"] = True
                    # Get the categories and their counts
                    categories = unique_values.head(20).to_dict()
                    col_meta["categories"] = [{"value": str(k), "count": int(v)} for k, v in categories.items()]
            
            # Try parsing datetime
            try:
                dt_series = pd.to_datetime(series, errors="coerce")
                if dt_series.notna().sum() > 0.5 * len(series):  # More than half are valid dates
                    col_meta["dtype_detected"] = "datetime"
                    col_meta["datetime_parts"] = {
                        "year": not dt_series.dt.year.isnull().all(),
                        "month": not dt_series.dt.month.isnull().all(),
                        "day": not dt_series.dt.day.isnull().all(),
                        "hour": not dt_series.dt.hour.isnull().all(),
                        "minute": not dt_series.dt.minute.isnull().all(),
                        "second": not dt_series.dt.second.isnull().all(),
                    }
                    
                    # Check for date patterns
                    if col_meta["datetime_parts"]["year"] and col_meta["datetime_parts"]["month"]:
                        if col_meta["datetime_parts"]["day"]:
                            if (col_meta["datetime_parts"]["hour"] or 
                                col_meta["datetime_parts"]["minute"] or 
                                col_meta["datetime_parts"]["second"]):
                                col_meta["date_pattern"] = "datetime"
                            else:
                                col_meta["date_pattern"] = "date"
                        else:
                            col_meta["date_pattern"] = "yearmonth"
                    else:
                        col_meta["date_pattern"] = "unknown"
            except Exception as e:
                # Failed to parse as datetime, continue with other analyses
                pass
            
            # Process numerical data
            try:
                if pd.api.types.is_numeric_dtype(series) or coerced_dtype in ["integer", "floating"]:
                    numeric_series = pd.to_numeric(series, errors="coerce")
                    
                    # Only calculate stats if we have valid numbers
                    if not numeric_series.isnull().all():
                        col_meta["numerical_stats"] = {
                            "min": float(numeric_series.min(skipna=True)),
                            "max": float(numeric_series.max(skipna=True)),
                            "min_row_index": int(numeric_series.idxmin()) if not pd.isna(numeric_series.idxmin()) else None,
                            "max_row_index": int(numeric_series.idxmax()) if not pd.isna(numeric_series.idxmax()) else None,
                            "mean": float(numeric_series.mean(skipna=True)),
                            "median": float(numeric_series.median(skipna=True)),
                            "std": float(numeric_series.std(skipna=True)) if len(numeric_series.dropna()) > 1 else None,
                            "histogram_bins": _create_histogram_bins(numeric_series),
                        }
            except Exception as e:
                # Failed to process as numeric, continue
                pass
                
            # Add column metadata to the DataFrame metadata
            df_metadata["columns"].append(col_meta)
        
        # Add sample data
        if df.shape[0] <= 10:
            df_metadata["sample"] = _safe_to_dict(df)
        else:
            # Use deterministic sampling for consistency
            sample_size = min(int(df.shape[0] * 0.05), 50)  # Cap at 50 rows for large DataFrames
            sample = df.sample(n=sample_size, random_state=42)
            df_metadata["sample"] = _safe_to_dict(sample)
        
        # Add column correlations if numeric columns exist
        numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
        if len(numeric_cols) > 1:
            try:
                corr_matrix = df[numeric_cols].corr().fillna(0).round(3)
                df_metadata["correlations"] = _safe_to_dict(corr_matrix, orient="split")
            except:
                # If correlation fails, skip it
                pass
        
        # Add DataFrame metadata to the list
        all_metadata.append(df_metadata)
    
    # Return the list of metadata dictionaries
    return all_metadata

def _safe_to_dict(df, orient="records"):
    """
    Safely convert DataFrame to dict, handling non-serializable objects.
    """
    try:
        return json.loads(df.to_json(orient=orient, date_format="iso"))
    except:
        # Fallback for non-serializable objects
        return df.astype(str).to_dict(orient=orient)

def _create_histogram_bins(series, bins=10):
    """
    Create histogram bin data for a numeric series.
    """
    try:
        # Drop NaN values before creating histogram
        clean_series = series.dropna()
        if len(clean_series) < 2:  # Need at least 2 data points
            return None
            
        hist, bin_edges = np.histogram(clean_series, bins=bins)
        return {
            "counts": hist.tolist(),
            "bin_edges": bin_edges.tolist()
        }
    except:
        return None

def analyze_project_data(project_id: int, df: Optional[pd.DataFrame] = None, source: str = "CSV") -> Dict:
    """
    Analyze data for a specific project.
    
    Args:
        project_id: The ID of the project to analyze
        df: Optional DataFrame to analyze. If None, will try to load from project sources.
        source: The source of the DataFrame (e.g., "CSV", "Salla")
        
    Returns:
        Dictionary containing the analysis metadata
    """
    from supabase_helpers.salla_order import get_salla_orders_for_project
    
    dataframes = []
    
    # If a DataFrame is provided, add it to the list
    if df is not None and not df.empty:
        dataframes.append((df, source))
    
    # Try to get Salla data if available
    try:
        salla_df = get_salla_orders_for_project(project_id)
        if salla_df is not None and not salla_df.empty:
            dataframes.append((salla_df, "Salla"))
    except Exception as e:
        print(f"Error loading Salla data for project {project_id}: {str(e)}")
    
    # If we have DataFrames to analyze, do so
    if dataframes:
        metadata = analyze_dataframes(dataframes)
        return {
            "project_id": project_id,
            "dataframes": metadata
        }
    else:
        # No data to analyze
        return {
            "project_id": project_id,
            "dataframes": []
        }
