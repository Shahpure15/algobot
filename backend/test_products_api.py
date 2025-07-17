#!/usr/bin/env python3
"""
Simple test script to verify the products API functionality works
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    # Test the delta exchange client
    from app.core.delta_exchange import DeltaExchangeClient, DeltaExchangeConfig
    
    # Initialize with dummy config
    config = DeltaExchangeConfig(
        api_key="test_key",
        api_secret="test_secret",
        base_url="https://api.delta.exchange"
    )
    
    client = DeltaExchangeClient(config)
    
    print("Testing Delta Exchange Client...")
    
    # Test products endpoint
    try:
        print("\n1. Testing get_products...")
        products = client.get_products_sync()
        print(f"Products result: {products.get('success', False)}")
        if products.get('success'):
            print(f"Number of products: {len(products.get('result', []))}")
    except Exception as e:
        print(f"Products test failed: {e}")
    
    # Test tickers endpoint
    try:
        print("\n2. Testing get_tickers...")
        tickers = client.get_tickers_sync()
        print(f"Tickers result: {tickers.get('success', False)}")
        if tickers.get('success'):
            print(f"Number of tickers: {len(tickers.get('result', []))}")
    except Exception as e:
        print(f"Tickers test failed: {e}")
    
    # Test specific product
    try:
        print("\n3. Testing get_product_by_symbol...")
        product = client.get_product_by_symbol_sync("BTCUSD")
        print(f"Product result: {product.get('success', False)}")
        if product.get('success'):
            print(f"Product symbol: {product.get('result', {}).get('symbol', 'N/A')}")
    except Exception as e:
        print(f"Product by symbol test failed: {e}")
    
    print("\nAll tests completed!")
    
except ImportError as e:
    print(f"Import error: {e}")
    print("Missing dependencies. Please install required packages.")
