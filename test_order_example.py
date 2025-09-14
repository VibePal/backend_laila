#!/usr/bin/env python3
"""
Test example for the order creation endpoint.
This shows how to create both regular orders and custom orders.
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "https://backend-laila.vercel.app/api/v1"
# For local testing, use: BASE_URL = "http://localhost:8000/api/v1"

# You'll need to get a valid JWT token from login first
# Replace this with your actual token
JWT_TOKEN = "your_jwt_token_here"

headers = {
    "Authorization": f"Bearer {JWT_TOKEN}",
    "Content-Type": "application/json"
}

def test_regular_order():
    """Test creating a regular order with normal products"""
    
    order_data = {
        "customer_name": "John Doe",
        "customer_contact": "+233123456789",
        "delivery_type": "delivery",
        "hostel": "Pentagon",
        "payment_type": "cash",
        "delivery_fee": 5.00,
        "special_notes": "Please deliver after 2 PM",
        "items": [
            {
                "product_id": "prod_123",
                "product_name": "Chocolate Cake",
                "quantity": 1,
                "unit_price": 25.00,
                "subtotal": 25.00,
                "is_custom_order": False,
                "is_free_ingredient": False
            },
            {
                "product_id": "prod_456",
                "product_name": "Vanilla Cupcakes",
                "quantity": 6,
                "unit_price": 3.00,
                "subtotal": 18.00,
                "is_custom_order": False,
                "is_free_ingredient": False
            }
        ],
        "total": 48.00,
        "order_date": "2024-01-15",
        "order_time": "2:30:00 PM",
        "created_by": "admin"
    }
    
    response = requests.post(f"{BASE_URL}/orders/", json=order_data, headers=headers)
    
    if response.status_code == 201:
        print("✅ Regular order created successfully!")
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"❌ Failed to create regular order: {response.status_code}")
        print(response.text)

def test_custom_order():
    """Test creating a custom order with custom pricing and free ingredients"""
    
    order_data = {
        "customer_name": "Sarah Johnson",
        "customer_contact": "+233987654321",
        "delivery_type": "pickup",
        "payment_type": "momo",
        "delivery_fee": 0.00,
        "special_notes": "Extra chocolate, please make it special for birthday",
        "items": [
            {
                "product_id": "custom-1704123456789",
                "product_name": "Custom Order - Colors: Pink, Blue, Inscription: Happy Birthday Sarah, Additional: ₵5.00",
                "quantity": 1,
                "unit_price": 25.00,
                "subtotal": 25.00,
                "is_custom_order": True,
                "custom_details": {
                    "base_price": 20.00,
                    "additional_price": 5.00,
                    "colors": "Pink, Blue",
                    "inscription": "Happy Birthday Sarah"
                }
            },
            {
                "product_id": "prod_789",
                "product_name": "Flour (Custom Order - Free)",
                "quantity": 2,
                "unit_price": 0.00,
                "subtotal": 0.00,
                "is_custom_order": False,
                "is_free_ingredient": True
            },
            {
                "product_id": "prod_101",
                "product_name": "Sugar (Custom Order - Free)",
                "quantity": 1,
                "unit_price": 0.00,
                "subtotal": 0.00,
                "is_custom_order": False,
                "is_free_ingredient": True
            }
        ],
        "total": 25.00,
        "order_date": "2024-01-15",
        "order_time": "3:45:00 PM",
        "created_by": "admin"
    }
    
    response = requests.post(f"{BASE_URL}/orders/", json=order_data, headers=headers)
    
    if response.status_code == 201:
        print("✅ Custom order created successfully!")
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"❌ Failed to create custom order: {response.status_code}")
        print(response.text)

def test_get_orders():
    """Test getting all orders"""
    
    response = requests.get(f"{BASE_URL}/orders/", headers=headers)
    
    if response.status_code == 200:
        print("✅ Orders retrieved successfully!")
        orders = response.json()
        print(f"Found {len(orders)} orders")
        for order in orders[:2]:  # Show first 2 orders
            print(f"- Order {order['id']}: {order['customer_name']} - ${order['total']}")
    else:
        print(f"❌ Failed to get orders: {response.status_code}")
        print(response.text)

def test_get_single_order(order_id):
    """Test getting a single order by ID"""
    
    response = requests.get(f"{BASE_URL}/orders/{order_id}", headers=headers)
    
    if response.status_code == 200:
        print(f"✅ Order {order_id} retrieved successfully!")
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"❌ Failed to get order {order_id}: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    print("🚀 Testing Order Creation Endpoint")
    print("=" * 50)
    
    # Note: You need to replace JWT_TOKEN with a valid token from login
    if JWT_TOKEN == "your_jwt_token_here":
        print("⚠️  Please update JWT_TOKEN with a valid token from login first!")
        print("   You can get a token by calling the login endpoint.")
        exit(1)
    
    print("\n1. Testing Regular Order Creation...")
    test_regular_order()
    
    print("\n2. Testing Custom Order Creation...")
    test_custom_order()
    
    print("\n3. Testing Get All Orders...")
    test_get_orders()
    
    print("\n4. Testing Get Single Order...")
    # Replace with an actual order ID from your database
    test_get_single_order("ORD-1704123456789")
    
    print("\n🎉 All tests completed!")
