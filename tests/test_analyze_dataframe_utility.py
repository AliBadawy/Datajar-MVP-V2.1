"""
Standalone Test for DataFrame Analysis Utility

This is a simplified test that directly imports and tests the analyze_dataframes 
functionality without any dependencies on API integration or authentication.
"""

import sys
import os
import pandas as pd
import numpy as np
import json

# Add Backend directory to path so we can import the utility
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Backend'))

# Import the analyze function
from utils.analyze_dataframes import analyze_dataframes


def create_sample_dataframe(rows=100):
    """Create a sample DataFrame with various data types for testing"""
    # Create sample data
    data = {
        'order_id': [f'ORD-{i:04d}' for i in range(1, rows+1)],
        'customer_name': [f'Customer {i}' for i in range(1, rows+1)],
        'order_date': pd.date_range(start='2024-01-01', periods=rows),
        'amount': np.random.uniform(50, 500, rows).round(2),
        'item_count': np.random.randint(1, 10, rows),
        'status': np.random.choice(['Pending', 'Shipped', 'Delivered', 'Cancelled'], rows),
        'payment_method': np.random.choice(['Credit Card', 'PayPal', 'Bank Transfer', 'Cash on Delivery'], rows),
        'notes': [f'Order note {i}' if i % 5 == 0 else None for i in range(1, rows+1)]
    }
    
    # Add some mixed data types to test detection
    mixed_data = []
    for i in range(rows):
        if i < rows*0.3:  # 30% integers
            mixed_data.append(i)
        elif i < rows*0.6:  # 30% string integers
            mixed_data.append(str(i))
        elif i < rows*0.9:  # 30% tagged strings
            mixed_data.append(f'Tag-{i}')
        else:  # 10% None
            mixed_data.append(None)
    
    data['mixed_column'] = mixed_data
    
    return pd.DataFrame(data)


def main():
    """Run a simple test of the DataFrame analysis functionality"""
    print("Creating sample DataFrame...")
    df = create_sample_dataframe(rows=100)
    print(f"Created DataFrame with {len(df)} rows and {len(df.columns)} columns")
    
    print("\nAnalyzing DataFrame...")
    metadata_list = analyze_dataframes([(df, "CSV")])
    
    print("\nAnalysis Results:")
    if not metadata_list:
        print("ERROR: No metadata generated!")
        return
    
    metadata = metadata_list[0]
    print(f"Source: {metadata['source']}")
    print(f"Total Rows: {metadata['total_rows']}")
    print(f"Total Columns: {metadata['total_columns']}")
    print(f"File Size: {metadata['file_size_mb']:.2f} MB")
    
    print("\nColumn Analysis:")
    for col_meta in metadata['columns']:
        print(f"\n  {col_meta['name']} ({col_meta['dtype_detected']}):")
        print(f"    Null Count: {col_meta['null_count']}")
        print(f"    Is Categorical: {col_meta['is_categorical']}")
        print(f"    Has Mixed Types: {col_meta['has_mixed_types']}")
        
        if col_meta['is_categorical']:
            print(f"    Categories: {len(col_meta.get('categories', []))} found")
            
        if col_meta['has_mixed_types']:
            print(f"    Mixed Types: {col_meta.get('mixed_types', [])}")
            
        if 'datetime_parts' in col_meta and any(col_meta['datetime_parts'].values()):
            print(f"    Detected as Date/Time with parts: {col_meta['datetime_parts']}")
            
        if col_meta.get('numerical_stats'):
            stats = col_meta['numerical_stats']
            print(f"    Min: {stats.get('min')}, Max: {stats.get('max')}")
            print(f"    Mean: {stats.get('mean')}, Median: {stats.get('median')}")
    
    print("\nSample Data:")
    print(f"  {len(metadata['sample'])} sample rows included")
    
    print("\nAnalysis Completed Successfully!")
    
    # Save the metadata to a JSON file for inspection
    with open('dataframe_analysis_results.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    print("\nResults saved to dataframe_analysis_results.json")


if __name__ == "__main__":
    main()
