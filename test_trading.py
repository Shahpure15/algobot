#!/usr/bin/env python3
"""
Test script for the new trading functionality
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_products():
    """Test products endpoint"""
    response = requests.get(f"{BASE_URL}/api/account/products")
    print("Products endpoint:")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        products = data.get('products', [])
        print(f"Found {len(products)} products")
        for product in products[:3]:  # Show first 3
            print(f"  - {product.get('symbol')}: {product.get('name')}")
    else:
        print(f"Error: {response.text}")
    print()

def test_live_orders():
    """Test live orders endpoint"""
    response = requests.get(f"{BASE_URL}/api/trading/live-orders")
    print("Live orders endpoint:")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            orders = data.get('result', [])
            print(f"Found {len(orders)} live orders")
            for order in orders[:3]:  # Show first 3
                print(f"  - {order.get('product_symbol')}: {order.get('side')} {order.get('size')} @ {order.get('limit_price')}")
        else:
            print(f"Warning: {data.get('error', 'Unknown error')}")
    else:
        print(f"Error: {response.text}")
    print()

def test_positions():
    """Test positions endpoint"""
    response = requests.get(f"{BASE_URL}/api/trading/positions")
    print("Positions endpoint:")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            positions = data.get('result', [])
            print(f"Found {len(positions)} positions")
            for position in positions[:3]:  # Show first 3
                print(f"  - {position.get('product_symbol')}: {position.get('size')} @ {position.get('entry_price')}")
        else:
            print(f"Warning: {data.get('error', 'Unknown error')}")
    else:
        print(f"Error: {response.text}")
    print()

def test_demo_orders():
    """Test demo orders endpoint"""
    response = requests.get(f"{BASE_URL}/api/trading/demo-orders")
    print("Demo orders endpoint:")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        orders = data.get('result', [])
        print(f"Found {len(orders)} demo orders")
        for order in orders:
            print(f"  - {order.get('product_symbol')}: {order.get('side')} {order.get('size')} @ {order.get('limit_price')}")
    else:
        print(f"Error: {response.text}")
    print()

def test_demo_positions():
    """Test demo positions endpoint"""
    response = requests.get(f"{BASE_URL}/api/trading/demo-positions")
    print("Demo positions endpoint:")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        positions = data.get('result', [])
        print(f"Found {len(positions)} demo positions")
        for position in positions:
            print(f"  - {position.get('product_symbol')}: {position.get('size')} @ {position.get('entry_price')} (PnL: {position.get('realized_pnl')})")
    else:
        print(f"Error: {response.text}")
    print()

def test_demo_trade():
    """Test demo trade endpoint"""
    order_data = {
        "symbol": "BTCUSD",
        "side": "buy",
        "quantity": "0.001",
        "price": "50000",
        "order_type": "limit_order"
    }
    
    response = requests.post(f"{BASE_URL}/api/trading/demo-trade", json=order_data)
    print("Demo trade endpoint:")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Demo order placed successfully: {data.get('delta_order_id')}")
        print(f"Local ID: {data.get('id')}, Status: {data.get('status')}")
    else:
        print(f"Error: {response.text}")
    print()

def test_place_order():
    """Test place order endpoint"""
    order_data = {
        "symbol": "BTCUSD",
        "side": "buy",
        "quantity": "0.001",
        "price": "50000",
        "order_type": "limit_order"
    }
    
    response = requests.post(f"{BASE_URL}/api/trading/trade", json=order_data)
    print("Place order endpoint:")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Order placed successfully: {data.get('delta_order_id')}")
    else:
        print(f"Error: {response.text}")
    print()

if __name__ == "__main__":
    print("Testing trading endpoints...")
    print("=" * 50)
    
    test_products()
    test_live_orders()
    test_positions()
    
    print("Testing demo endpoints...")
    print("-" * 30)
    test_demo_orders()
    test_demo_positions()
    test_demo_trade()
    
    # Uncomment to test placing a real order (be careful with real API keys)
    # test_place_order()
    
    print("Testing complete!")
