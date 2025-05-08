import requests
import pandas as pd
from typing import List, Dict, Any

def get_salla_orders(access_token: str, from_date: str, to_date: str, max_pages: int = 5, timeout: int = 10) -> List[Dict[str, Any]]:
    """
    Fetch orders from Salla API for a specific date range with performance optimizations.
    
    Args:
        access_token (str): Salla API access token
        from_date (str): Start date in format YYYY-MM-DD
        to_date (str): End date in format YYYY-MM-DD
        max_pages (int, optional): Maximum number of pages to fetch. Defaults to 5 for performance.
        timeout (int, optional): Request timeout in seconds. Defaults to 10.
        
    Returns:
        List[Dict[str, Any]]: List of order objects
    """
    url = "https://api.salla.dev/admin/v2/orders"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }
    
    params = {
        "from_date": from_date,
        "to_date": to_date,
        "per_page": 100  # Increased pagination to reduce number of requests
    }
    
    print(f"Making initial request to Salla API with timeout={timeout}s")
    try:
        response = requests.get(url, headers=headers, params=params, timeout=timeout)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        print("Salla API request timed out. Consider increasing the timeout value.")
        return []
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from Salla API: {str(e)}")
        return []
    
    data = response.json()
    orders = data.get("data", [])
    print(f"Received {len(orders)} orders from first page")
    
    # Handle pagination with limits for performance
    next_page_url = data.get("pagination", {}).get("next_page_url")
    page_count = 1
    
    while next_page_url and page_count < max_pages:
        print(f"Fetching page {page_count + 1} from {next_page_url}")
        try:
            response = requests.get(next_page_url, headers=headers, timeout=timeout)
            response.raise_for_status()
            
            data = response.json()
            page_orders = data.get("data", [])
            print(f"Received {len(page_orders)} orders from page {page_count + 1}")
            
            orders.extend(page_orders)
            next_page_url = data.get("pagination", {}).get("next_page_url")
            page_count += 1
        except Exception as e:
            print(f"Error fetching page {page_count + 1}: {str(e)}")
            break
    
    if next_page_url and page_count >= max_pages:
        print(f"WARNING: Reached maximum page limit ({max_pages}). Some orders may not be included.")
    
    print(f"Completed Salla API requests. Retrieved {len(orders)} orders in total.")
    return orders

def get_all_salla_orders(access_token: str, from_date: str, to_date: str) -> List[Dict[str, Any]]:
    """
    Fetches all orders from Salla API between from_date and to_date, handling pagination.
    
    Args:
        access_token (str): OAuth token from Salla.
        from_date (str): ISO date format string (e.g. "2024-01-01").
        to_date (str): ISO date format string (e.g. "2024-01-31").

    Returns:
        List[Dict]: A complete list of all order records across all pages.
    """
    url = "https://api.salla.dev/admin/v2/orders"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    params = {
        "from_date": from_date,
        "to_date": to_date,
        "per_page": 100,
        "page": 1
    }
    
    all_orders = []
    has_more = True
    
    while has_more:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        orders = data.get("data", [])
        all_orders.extend(orders)
        
        # Check if there's another page
        pagination = data.get("pagination", {})
        current_page = pagination.get("current_page", 1)
        last_page = pagination.get("last_page", 1)
        
        if current_page >= last_page:
            has_more = False
        else:
            params["page"] = current_page + 1
    
    return all_orders

def normalize_salla_orders(orders: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Normalizes Salla orders data for analysis by flattening nested structures.
    
    Args:
        orders (List[Dict]): List of raw order objects from Salla API.
        
    Returns:
        List[Dict]: List of normalized/flattened order records suitable for DataFrame conversion.
    """
    normalized_orders = []
    
    for order in orders:
        # Extract date information
        date_obj = order.get("date", {})
        date_str = date_obj.get("date") if isinstance(date_obj, dict) else str(date_obj)
        
        # Extract total and currency
        total_obj = order.get("total", {})
        total_amount = total_obj.get("amount") if isinstance(total_obj, dict) else None
        currency = total_obj.get("currency") if isinstance(total_obj, dict) else None
        
        # Extract status information
        status_obj = order.get("status", {})
        status_name = status_obj.get("name") if isinstance(status_obj, dict) else None
        status_slug = status_obj.get("slug") if isinstance(status_obj, dict) else None
        
        # Process items
        items = order.get("items", [])
        items_count = len(items)
        items_names = [item.get("name") for item in items if item.get("name")]
        items_quantities = [item.get("quantity") for item in items if item.get("quantity")]
        total_quantity = sum(items_quantities) if items_quantities else 0
        
        # Extract exchange rate if available
        exchange_rate_obj = order.get("exchange_rate", {})
        exchange_rate = exchange_rate_obj.get("rate") if isinstance(exchange_rate_obj, dict) else None
        exchange_currency = exchange_rate_obj.get("exchange_currency") if isinstance(exchange_rate_obj, dict) else None
        
        # Create a base normalized order with flattened fields
        normalized_order = {
            "id": order.get("id"),
            "reference_id": order.get("reference_id"),
            "status": status_name,
            "status_slug": status_slug,
            "date": date_str,
            "currency": currency,
            "total": total_amount,
            "can_cancel": order.get("can_cancel", False),
            "can_reorder": order.get("can_reorder", False),
            "payment_method": order.get("payment_method"),
            "is_pending_payment": order.get("is_pending_payment", False),
            "pending_payment_ends_at": order.get("pending_payment_ends_at"),
            "items_count": items_count,
            "total_quantity": total_quantity,
            "items_names": ", ".join(items_names) if items_names else "",
            "is_digital": order.get("features", {}).get("digitalable") if isinstance(order.get("features"), dict) else False,
            "is_shippable": order.get("features", {}).get("shippable") if isinstance(order.get("features"), dict) else False,
            "exchange_rate": exchange_rate,
            "exchange_currency": exchange_currency
        }
        
        normalized_orders.append(normalized_order)
    
    return normalized_orders

def convert_orders_to_df(orders: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Converts a list of Salla orders to a pandas DataFrame for analysis.
    
    Args:
        orders (List[Dict]): List of order objects from Salla API
        
    Returns:
        pd.DataFrame: DataFrame containing structured order data
    """
    # First normalize the orders to flatten the nested structure
    normalized_orders = normalize_salla_orders(orders)
    
    # Convert to DataFrame
    df = pd.DataFrame(normalized_orders)
    
    # Process date columns if present
    if 'date' in df.columns:
        try:
            # Try to convert date strings to pandas datetime
            df['order_date'] = pd.to_datetime(df['date'])
            # Extract useful date components
            df['order_year'] = df['order_date'].dt.year
            df['order_month'] = df['order_date'].dt.month
            df['order_day'] = df['order_date'].dt.day
            df['order_day_of_week'] = df['order_date'].dt.dayofweek
        except Exception as e:
            print(f"Warning: Could not process date columns: {e}")
    
    # Add calculated fields that might be useful for analysis
    if 'total' in df.columns and 'total_quantity' in df.columns:
        try:
            # Calculate average item price where quantity > 0
            mask = df['total_quantity'] > 0
            df.loc[mask, 'avg_item_price'] = df.loc[mask, 'total'] / df.loc[mask, 'total_quantity']
        except Exception as e:
            print(f"Warning: Could not calculate average item price: {e}")
            
    return df
