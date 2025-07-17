#!/usr/bin/env python3
"""
Simple test script to verify the trading bot API endpoints
"""
import asyncio
import httpx
import json

BASE_URL = "http://localhost:8000"

async def test_api_endpoints():
    """Test basic API endpoints"""
    print("🚀 Testing Trading Bot API endpoints...")
    
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # Test health endpoint
        print("\n📊 Testing health endpoint...")
        try:
            response = await client.get("/health")
            print(f"✅ Health check: {response.status_code} - {response.json()}")
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return
        
        # Test root endpoint
        print("\n🏠 Testing root endpoint...")
        try:
            response = await client.get("/")
            print(f"✅ Root endpoint: {response.status_code} - {response.json()}")
        except Exception as e:
            print(f"❌ Root endpoint failed: {e}")
        
        # Test connection status
        print("\n🔌 Testing connection status...")
        try:
            response = await client.get("/api/auth/status")
            print(f"✅ Connection status: {response.status_code} - {response.json()}")
        except Exception as e:
            print(f"❌ Connection status failed: {e}")
        
        # Test trading stats
        print("\n📈 Testing trading statistics...")
        try:
            response = await client.get("/api/history/stats")
            print(f"✅ Trading stats: {response.status_code} - {response.json()}")
        except Exception as e:
            print(f"❌ Trading stats failed: {e}")
        
        # Test trade history
        print("\n📋 Testing trade history...")
        try:
            response = await client.get("/api/history/trades")
            print(f"✅ Trade history: {response.status_code} - Found {len(response.json())} trades")
        except Exception as e:
            print(f"❌ Trade history failed: {e}")
        
        # Test chart data
        print("\n📊 Testing chart data...")
        try:
            response = await client.get("/api/history/chart-data")
            data = response.json()
            print(f"✅ Chart data: {response.status_code} - {len(data['daily_trades'])} daily entries, {len(data['symbol_distribution'])} symbols")
        except Exception as e:
            print(f"❌ Chart data failed: {e}")
        
        print("\n🎉 API testing completed!")

if __name__ == "__main__":
    print("=" * 60)
    print("🤖 Algo Trading Bot - API Test Suite")
    print("=" * 60)
    print("\nMake sure the application is running with:")
    print("  docker-compose up --build")
    print("\nThen access the dashboard at: http://localhost:3000")
    print("=" * 60)
    
    asyncio.run(test_api_endpoints())
