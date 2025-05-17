import json
import random
from datetime import datetime, timedelta
import uuid

def generate_fake_salla_orders(num_orders=10, project_id=1):
    """
    Generate fake Salla orders data that matches the expected format from the Salla API.
    
    Args:
        num_orders (int): Number of orders to generate
        project_id (int): Project ID to associate with orders
        
    Returns:
        dict: A dictionary with the request format for Postman
    """
    # Product options to choose from for variety
    products = [
        {"name": "T-shirt", "price": 99.99, "sku": "TSH001"},
        {"name": "Jeans", "price": 199.99, "sku": "JNS002"},
        {"name": "Sneakers", "price": 349.99, "sku": "SNK003"},
        {"name": "Watch", "price": 599.99, "sku": "WTC004"},
        {"name": "Backpack", "price": 149.99, "sku": "BKP005"},
        {"name": "Sunglasses", "price": 129.99, "sku": "SGL006"},
        {"name": "Hat", "price": 79.99, "sku": "HAT007"},
        {"name": "Hoodie", "price": 179.99, "sku": "HOD008"}
    ]
    
    # Status options
    statuses = [
        {"name": "Completed", "slug": "completed"},
        {"name": "Processing", "slug": "processing"},
        {"name": "Pending", "slug": "pending"},
        {"name": "Cancelled", "slug": "cancelled"}
    ]
    
    # Generate orders
    orders = []
    for i in range(num_orders):
        # Generate random date within the last 30 days
        order_date = datetime.now() - timedelta(days=random.randint(0, 30))
        order_date_str = order_date.strftime("%Y-%m-%d %H:%M:%S")
        
        # Generate 1-5 random items per order
        num_items = random.randint(1, 5)
        items = []
        total_amount = 0
        
        for j in range(num_items):
            product = random.choice(products)
            quantity = random.randint(1, 3)
            item_total = product["price"] * quantity
            total_amount += item_total
            
            item = {
                "id": str(uuid.uuid4())[:8],
                "name": product["name"],
                "sku": product["sku"],
                "quantity": quantity,
                "price": {
                    "amount": product["price"],
                    "currency": "SAR"
                },
                "total": {
                    "amount": item_total,
                    "currency": "SAR"
                }
            }
            items.append(item)
        
        # Generate the order
        status = random.choice(statuses)
        order = {
            "id": str(1000000 + i),
            "reference_id": f"INV-{2023000 + i}",
            "status": status,
            "date": {
                "date": order_date_str,
                "timezone_type": 3,
                "timezone": "Asia/Riyadh"
            },
            "total": {
                "amount": total_amount,
                "currency": "SAR"
            },
            "can_cancel": status["slug"] in ["pending", "processing"],
            "can_reorder": status["slug"] == "completed",
            "payment_method": random.choice(["card", "cod", "bank_transfer", "apple_pay"]),
            "is_pending_payment": status["slug"] == "pending",
            "pending_payment_ends_at": None,
            "items": items,
            "features": {
                "digitalable": random.choice([True, False]),
                "shippable": random.choice([True, False])
            },
            "exchange_rate": {
                "rate": 3.75,
                "exchange_currency": "USD"
            }
        }
        orders.append(order)
    
    # Format for the API request
    request_body = {
        "project_id": project_id,
        "orders": orders
    }
    
    return request_body

if __name__ == "__main__":
    # Generate 20 fake orders for project ID 1
    fake_data = generate_fake_salla_orders(20, 1)
    
    # Write to a file for convenience
    with open("fake_salla_orders.json", "w") as f:
        json.dump(fake_data, f, indent=2)
    
    print(f"Generated {len(fake_data['orders'])} fake Salla orders for project {fake_data['project_id']}")
    print("Data saved to fake_salla_orders.json")