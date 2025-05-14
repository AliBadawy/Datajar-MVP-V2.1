"""
Test Suite for DataFrame Analysis Utility

These tests verify the functionality of the DataFrame analysis utility, which is responsible
for profiling uploaded DataFrames, detecting data types, and generating metadata.
"""

import sys
import os
import pandas as pd
import numpy as np
import pytest
from typing import List, Dict, Tuple, Any

# Add Backend directory to path so we can import the utility
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'Backend'))

# Import the analyze functions
from utils.analyze_dataframes import analyze_dataframes, _create_histogram_bins, _safe_to_dict


@pytest.fixture
def sample_dataframe() -> pd.DataFrame:
    """Create a sample DataFrame with various data types for testing"""
    # Create sample data
    data = {
        'order_id': [f'ORD-{i:04d}' for i in range(1, 101)],
        'customer_name': [f'Customer {i}' for i in range(1, 101)],
        'order_date': pd.date_range(start='2024-01-01', periods=100),
        'amount': np.random.uniform(50, 500, 100).round(2),
        'item_count': np.random.randint(1, 10, 100),
        'status': np.random.choice(['Pending', 'Shipped', 'Delivered', 'Cancelled'], 100),
        'payment_method': np.random.choice(['Credit Card', 'PayPal', 'Bank Transfer', 'Cash on Delivery'], 100),
        'notes': [f'Order note {i}' if i % 5 == 0 else None for i in range(1, 101)]
    }
    
    # Add some mixed data types to test detection
    mixed_data = []
    for i in range(100):
        if i < 30:
            mixed_data.append(i)
        elif i < 60:
            mixed_data.append(str(i))
        elif i < 90:
            mixed_data.append(f'Tag-{i}')
        else:
            mixed_data.append(None)
    
    data['mixed_column'] = mixed_data
    
    return pd.DataFrame(data)


@pytest.fixture
def empty_dataframe() -> pd.DataFrame:
    """Create an empty DataFrame for testing edge cases"""
    return pd.DataFrame()


def test_analyze_dataframes_structure(sample_dataframe):
    """Test that the analyze_dataframes function returns the expected structure"""
    # Analyze a single DataFrame
    metadata_list = analyze_dataframes([(sample_dataframe, "CSV")])
    
    # Check basic structure
    assert isinstance(metadata_list, list)
    assert len(metadata_list) == 1
    
    metadata = metadata_list[0]
    assert isinstance(metadata, dict)
    assert "source" in metadata
    assert metadata["source"] == "CSV"
    assert "total_rows" in metadata
    assert metadata["total_rows"] == 100
    assert "total_columns" in metadata
    assert metadata["total_columns"] == 9
    assert "columns" in metadata
    assert isinstance(metadata["columns"], list)
    assert "sample" in metadata
    assert isinstance(metadata["sample"], list)


def test_analyze_dataframes_columns(sample_dataframe):
    """Test that column metadata is correctly generated"""
    metadata_list = analyze_dataframes([(sample_dataframe, "CSV")])
    metadata = metadata_list[0]
    
    # There should be metadata for each column
    assert len(metadata["columns"]) == 9
    
    # Check column metadata structure
    for col_meta in metadata["columns"]:
        assert "name" in col_meta
        assert "original_dtype" in col_meta
        assert "dtype_detected" in col_meta
        assert "null_count" in col_meta
        assert "sample_values" in col_meta
        assert "has_mixed_types" in col_meta
        assert "is_categorical" in col_meta
        
    # Test a specific column - mixed_column should be detected as having mixed types
    mixed_col_meta = next((cm for cm in metadata["columns"] if cm["name"] == "mixed_column"), None)
    assert mixed_col_meta is not None
    assert mixed_col_meta["has_mixed_types"] is True
    assert "mixed_types" in mixed_col_meta
    assert len(mixed_col_meta["mixed_types"]) > 1
    
    # Test datetime detection
    date_col_meta = next((cm for cm in metadata["columns"] if cm["name"] == "order_date"), None)
    assert date_col_meta is not None
    assert "datetime_parts" in date_col_meta
    assert date_col_meta["datetime_parts"]["year"] is True
    assert date_col_meta["datetime_parts"]["month"] is True
    assert date_col_meta["datetime_parts"]["day"] is True


def test_analyze_dataframes_numeric_stats(sample_dataframe):
    """Test that numerical statistics are correctly computed"""
    metadata_list = analyze_dataframes([(sample_dataframe, "CSV")])
    metadata = metadata_list[0]
    
    # Check that numeric columns have statistics
    amount_meta = next((cm for cm in metadata["columns"] if cm["name"] == "amount"), None)
    assert amount_meta is not None
    assert "numerical_stats" in amount_meta
    stats = amount_meta["numerical_stats"]
    
    # Verify statistics fields
    assert "min" in stats
    assert "max" in stats
    assert "mean" in stats
    assert "median" in stats
    assert "min_row_index" in stats
    assert "max_row_index" in stats
    assert "histogram_bins" in stats


def test_analyze_dataframes_categorical(sample_dataframe):
    """Test that categorical data is correctly identified"""
    metadata_list = analyze_dataframes([(sample_dataframe, "CSV")])
    metadata = metadata_list[0]
    
    # Check status column which should be categorical
    status_meta = next((cm for cm in metadata["columns"] if cm["name"] == "status"), None)
    assert status_meta is not None
    assert status_meta["is_categorical"] is True
    assert "categories" in status_meta
    assert len(status_meta["categories"]) <= 10  # Should have 4 categories


def test_analyze_dataframes_empty(empty_dataframe):
    """Test handling of empty DataFrames"""
    # This shouldn't raise any exceptions
    metadata_list = analyze_dataframes([(empty_dataframe, "CSV")])
    assert isinstance(metadata_list, list)
    
    # No output for empty DataFrame
    assert len(metadata_list) == 0


def test_analyze_multiple_dataframes(sample_dataframe):
    """Test analyzing multiple DataFrames at once"""
    # Create a second, smaller DataFrame
    small_df = sample_dataframe.head(20).copy()
    
    # Analyze both
    metadata_list = analyze_dataframes([
        (sample_dataframe, "CSV"),
        (small_df, "Salla")
    ])
    
    # Check results
    assert len(metadata_list) == 2
    assert metadata_list[0]["source"] == "CSV"
    assert metadata_list[0]["total_rows"] == 100
    assert metadata_list[1]["source"] == "Salla"
    assert metadata_list[1]["total_rows"] == 20
