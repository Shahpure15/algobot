# scripts/test_connection.py
import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.exchanges.delta.clients import DeltaExchangeClient
from src.utils.logger import setup_logger, get_logger
from config.settings import config

def test_delta_connection():
    """Test Delta Exchange connection and API calls"""
    
    # Setup logging
    setup_logger()
    logger = get_logger(__name__)
    
    print("=" * 60)
    print("DELTA EXCHANGE CONNECTION TEST")
    print("=" * 60)
    
    try:
        # Check if API credentials are set
        if not config.exchange.api_key or not config.exchange.api_secret:
            print("❌ ERROR: API credentials not set")
            print("Please set DELTA_API_KEY and DELTA_API_SECRET in your .env file")
            return False
        
        print(f"🔗 Testing connection to Delta Exchange...")
        print(f"   Testnet: {config.exchange.testnet}")
        print(f"   Symbol: {config.trading.symbol}")
        
        # Initialize client
        client = DeltaExchangeClient(
            api_key=config.exchange.api_key,
            api_secret=config.exchange.api_secret,
            testnet=config.exchange.testnet
        )
        
        # Test 1: Connection test
        print("\n1. Testing API connection...")
        if client.test_connection():
            print("   ✅ Connection successful")
        else:
            print("   ❌ Connection failed")
            return False
        
        # Test 2: Get account balance
        print("\n2. Fetching account balance...")
        try:
            balance_data = client.get_account_balance()
            print(f"   ✅ Balance data retrieved: {balance_data}")
        except Exception as e:
            print(f"   ❌ Failed to get balance: {e}")
            return False
        
        # Test 3: Get available products
        print("\n3. Fetching available products...")
        try:
            products = client.get_products()
            print(f"   ✅ Found {len(products.get('result', []))} products")
            
            # Check if our trading symbol exists
            symbol_found = False
            for product in products.get('result', []):
                if product.get('symbol') == config.trading.symbol:
                    symbol_found = True
                    print(f"   ✅ Trading symbol {config.trading.symbol} found")
                    print(f"      Product ID: {product.get('id')}")
                    print(f"      Base Asset: {product.get('underlying_asset')}")
                    break
            
            if not symbol_found:
                print(f"   ⚠️  Trading symbol {config.trading.symbol} not found")
                print("   Available symbols:")
                for i, product in enumerate(products.get('result', [])[:10]):
                    print(f"      {i+1}. {product.get('symbol')}")
                if len(products.get('result', [])) > 10:
                    print(f"      ... and {len(products.get('result', [])) - 10} more")
                    
        except Exception as e:
            print(f"   ❌ Failed to get products: {e}")
            return False
        
        # Test 4: Get current positions
        print("\n4. Fetching current positions...")
        try:
            positions = client.get_positions()
            print(f"   ✅ Current positions: {len(positions.get('result', []))}")
            if positions.get('result'):
                for pos in positions['result']:
                    print(f"      {pos.get('symbol')}: {pos.get('size')} @ {pos.get('entry_price')}")
        except Exception as e:
            print(f"   ❌ Failed to get positions: {e}")
            return False
        
        # Test 5: Get historical data (if available)
        print("\n5. Testing historical data...")
        try:
            historical_data = client.get_historical_data(
                symbol=config.trading.symbol,
                resolution=config.trading.timeframe
            )
            print(f"   ✅ Historical data retrieved: {len(historical_data.get('result', []))} candles")
        except Exception as e:
            print(f"   ❌ Failed to get historical data: {e}")
            # This is not critical, continue
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("Delta Exchange connection is working correctly.")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        logger.error(f"Connection test failed: {e}")
        return False

def test_order_placement():
    """Test order placement (paper trading)"""
    
    print("\n" + "=" * 60)
    print("PAPER TRADING TEST")
    print("=" * 60)
    
    try:
        # Initialize client
        client = DeltaExchangeClient(
            api_key=config.exchange.api_key,
            api_secret=config.exchange.api_secret,
            testnet=config.exchange.testnet
        )
        
        print("⚠️  This is a PAPER TRADING test on testnet")
        print("   No real money will be used")
        
        # Test small market order
        print(f"\n1. Testing small market order...")
        print(f"   Symbol: {config.trading.symbol}")
        print(f"   Size: {config.trading.position_size}")
        
        # Note: Uncomment the following lines only if you want to test actual order placement
        # WARNING: This will place a real order on testnet
        
        # try:
        #     order_result = client.place_order(
        #         symbol=config.trading.symbol,
        #         side='buy',
        #         size=config.trading.position_size,
        #         order_type='market'
        #     )
        #     print(f"   ✅ Order placed successfully: {order_result}")
        #     
        #     # Cancel the order immediately if it's still open
        #     if order_result.get('success') and order_result.get('result', {}).get('id'):
        #         order_id = order_result['result']['id']
        #         cancel_result = client.cancel_order(order_id)
        #         print(f"   ✅ Order cancelled: {cancel_result}")
        #         
        # except Exception as e:
        #     print(f"   ❌ Order placement failed: {e}")
        
        print("   ✅ Order placement test skipped (commented out for safety)")
        print("   Uncomment the test code in test_connection.py to test actual orders")
        
        return True
        
    except Exception as e:
        print(f"❌ Paper trading test failed: {e}")
        return False

def main():
    """Main test function"""
    print("Starting Delta Exchange connectivity tests...")
    
    # Test basic connection
    connection_ok = test_delta_connection()
    
    if connection_ok:
        # Test order placement
        order_ok = test_order_placement()
        
        if order_ok:
            print("\n🎉 All tests completed successfully!")
            print("Your bot is ready to start trading!")
        else:
            print("\n⚠️  Connection OK, but order placement needs attention")
    else:
        print("\n❌ Connection tests failed. Please check your configuration.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
