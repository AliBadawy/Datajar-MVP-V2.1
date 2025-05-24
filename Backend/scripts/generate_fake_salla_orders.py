#!/usr/bin/env python3
"""
Script to generate fake Salla orders and save them to Supabase.
This can be used to populate test data for a specific project.

Usage:
    python generate_fake_salla_orders.py --project_id 123 --count 50

Arguments:
    --project_id: The project ID to associate with the generated orders
    --count: Number of fake orders to generate (default: 20)
"""

import sys
import os
import argparse
import random
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
from faker import Faker

# Add the parent directory to the path so we can import from the Backend modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from supabase_helpers.salla_order import save_salla_orders
from supabase_helpers.project import get_project_by_id

# Initialize Faker
fake = Faker('ar_SA')  # Arabic locale for Saudi Arabia

# Constants for generating realistic data
STATUSES = [
    'بإنتظار المراجعة',
    'تم الشحن', 
    'تم التوصيل', 
    'تم الإلغاء', 
    'قيد المعالجة',
    'مكتمل'
]

CURRENCIES = ['SAR', 'USD', 'AED', 'KWD']

ITEM_NAMES = [
    'فستان', 
    'قميص', 
    'سروال', 
    'حذاء', 
    'حقيبة',
    'قبعة',
    'نظارة شمسية',
    'ساعة',
    'هاتف محمول',
    'سماعات',
    'شاحن',
    'حافظة هاتف'
]

PAYMENT_METHODS = [
    'bank', 
    'credit_card', 
    'apple_pay', 
    'cash_on_delivery',
    'stc_pay',
    'mada'
]

COUNTRIES = [
    'المملكة العربية السعودية',
    'الإمارات العربية المتحدة',
    'الكويت',
    'قطر',
    'البحرين',
    'عمان',
    'مصر',
    'الأردن'
]

def generate_fake_orders(project_id, count=20):
    """Generate a DataFrame with fake Salla orders"""
    
    orders = []
    
    # Generate random dates within the last 90 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    
    for i in range(count):
        # Generate a random date
        order_date = fake.date_time_between(start_date=start_date, end_date=end_date)
        
        # Sometimes leave customer fields empty to match the observed data pattern
        include_customer = random.random() > 0.3
        customer_name = fake.name() if include_customer else None
        customer_country = random.choice(COUNTRIES) if include_customer else None
        
        # Generate item details - using fields that match the Supabase schema
        item_name = random.choice(ITEM_NAMES)
        
        # More realistic item quantities (usually between 1-10 with occasional larger orders)
        item_quantity = max(1, int(np.random.exponential(scale=2)))
        if random.random() < 0.1:  # 10% chance of bulk order
            item_quantity = random.randint(10, 100)
        
        # Generate realistic price per item and total amount
        # Each item type has a different price range
        if item_name in ['فستان', 'حذاء']:
            # Expensive items
            price_per_item = random.randint(200, 800) * 10  # 2000-8000 SAR
        elif item_name in ['قميص', 'سروال', 'حقيبة', 'ساعة']:
            # Mid-range items
            price_per_item = random.randint(100, 300) * 10  # 1000-3000 SAR
        else:
            # Cheaper items
            price_per_item = random.randint(20, 100) * 10  # 200-1000 SAR
            
        # Calculate total amount based on price and quantity
        total_amount = price_per_item * item_quantity
        
        # Generate a completely random 10-digit order ID like 1365112266
        order_id_str = str(random.randint(1000000000, 9999999999))
        
        # Create complete order data - making sure all fields match the Supabase schema
        order = {
            # Key fields highlighted by the user
            'order_id': order_id_str,  # Using string format
            'project_id': project_id,
            'total_amount': total_amount,  # Based on price_per_item * quantity
            'item_name': item_name,
            'item_quantity': item_quantity,
            
            # Other required fields
            'status': random.choice(STATUSES),
            'currency': 'SAR',  # Default to SAR for Saudi Arabia
            'order_date': order_date,
            'customer_name': customer_name,
            'customer_country': customer_country,
            'payment_method': random.choice(PAYMENT_METHODS),
            
            # Include price_per_item for reference (though not directly saved)
            'price_per_item': price_per_item
        }
        
        orders.append(order)
    
    return pd.DataFrame(orders)

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Generate fake Salla orders and save to Supabase')
    parser.add_argument('--project_id', type=int, default=119, help='Project ID to associate orders with (default: 118)')
    parser.add_argument('--count', type=int, default=20, help='Number of fake orders to generate')
    
    args = parser.parse_args()
    
    # Use default project ID 118 if not specified
    project_id = args.project_id
    
    # Verify the project exists
    project = get_project_by_id(project_id)
    if not project:
        print(f"Error: Project with ID {project_id} not found.")
        sys.exit(1)
    
    print(f"Generating {args.count} fake orders for project {project_id} ({project.get('name', 'Unknown')})")
    
    # Generate fake orders
    orders_df = generate_fake_orders(project_id, args.count)
    
    # Print detailed sample of the data
    print("\nSample of generated orders:")
    
    # Display key fields in a more readable format
    sample_data = orders_df.head(3)
    print("\nKEY FIELDS SAMPLE:")
    for i, row in sample_data.iterrows():
        print(f"Order #{i+1}:")
        print(f"  Order ID: {row['order_id']}")
        print(f"  Item: {row['item_name']} x {row['item_quantity']}")
        print(f"  Price per item: {row.get('price_per_item', 'N/A')} SAR")
        print(f"  Total amount: {row['total_amount']} SAR")
        print(f"  Status: {row['status']}")
        print()
    
    print(f"Total orders generated: {len(orders_df)}")
    
    # Add column information to help with debugging
    print("\nColumns in the DataFrame:")
    for col in orders_df.columns:
        print(f"  - {col}")
        
    # Remove price_per_item as it's not needed for Supabase
    if 'price_per_item' in orders_df.columns:
        orders_df = orders_df.drop('price_per_item', axis=1)
        
    # Rename columns to match what Supabase helper expects
    # Based on the mapping in save_salla_orders function
    column_mapping = {
        'total_amount': 'total',  # Map back to what Supabase helper expects
        'item_name': 'items_names',
        'item_quantity': 'total_quantity'
    }
    orders_df = orders_df.rename(columns=column_mapping)
    
    # Important: Let the save_salla_orders function handle the date formatting
    # We keep order_date as datetime objects in our DataFrame
    
    print("\nAfter column mapping for Supabase:")
    print(f"Columns: {orders_df.columns.tolist()}")
    print("Sample row:") 
    print(orders_df.iloc[0].to_dict())
    
    # Save to Supabase
    print("\nSaving orders to Supabase...")
    result = save_salla_orders(project_id, orders_df)
    
    # Print result
    if result.get('count', 0) > 0:
        print(f"Success! {result.get('count')} orders saved to Supabase.")
    else:
        print(f"Error saving orders: {result.get('error', 'Unknown error')}")
        print(f"Message: {result.get('message', '')}")
    
    print("\nDone!")

if __name__ == "__main__":
    main()
