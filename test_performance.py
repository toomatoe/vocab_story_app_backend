"""
Performance testing script to demonstrate efficiency improvements
"""
import time
import requests
import json
from typing import List, Dict, Any

BASE_URL = "http://127.0.0.1:8001"

def test_performance():
    """Test API performance with repeated requests"""
    
    print("🚀 EFFICIENCY TESTING - Optimized Vocabulary Story API")
    print("=" * 60)
    
    # Test cases
    test_cases = [
        {"word": "efficiency", "length": "brief"},
        {"word": "performance", "length": "short"},
        {"word": "optimization", "length": "medium"},
        {"word": "efficiency", "length": "brief"},  # Repeat for cache test
        {"word": "performance", "length": "short"}, # Repeat for cache test
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"📊 Test {i}: {test_case['word']} ({test_case['length']})")
        
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{BASE_URL}/generate_story",
                json=test_case,
                timeout=10
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            if response.status_code == 200:
                data = response.json()
                word_count = len(data["story"].split())
                
                result = {
                    "test": i,
                    "word": test_case["word"],
                    "length": test_case["length"],
                    "response_time": response_time,
                    "word_count": word_count,
                    "mock_mode": data["mock"],
                    "status": "✅ Success"
                }
                
                print(f"   ⏱️  Response time: {response_time:.2f}s")
                print(f"   📝 Word count: {word_count}")
                print(f"   🤖 Mock mode: {data['mock']}")
                print(f"   {result['status']}")
                
            else:
                result = {
                    "test": i,
                    "word": test_case["word"],
                    "length": test_case["length"],
                    "response_time": response_time,
                    "status": f"❌ Error {response.status_code}",
                    "error": response.text
                }
                print(f"   {result['status']}: {response.text}")
                
        except requests.exceptions.Timeout:
            result = {
                "test": i,
                "word": test_case["word"],
                "length": test_case["length"],
                "status": "⏰ Timeout"
            }
            print(f"   {result['status']}")
            
        except Exception as e:
            result = {
                "test": i,
                "word": test_case["word"],
                "length": test_case["length"],
                "status": f"❌ Error: {e}"
            }
            print(f"   {result['status']}")
        
        results.append(result)
        print()
    
    # Performance analysis
    print("📈 PERFORMANCE ANALYSIS")
    print("=" * 30)
    
    successful_tests = [r for r in results if "response_time" in r]
    if successful_tests:
        avg_time = sum(r["response_time"] for r in successful_tests) / len(successful_tests)
        print(f"Average response time: {avg_time:.2f}s")
        
        # Check for cache effectiveness
        repeated_requests = [r for r in successful_tests if r["test"] > 3]  # Tests 4 and 5 are repeats
        if repeated_requests:
            cache_avg = sum(r["response_time"] for r in repeated_requests) / len(repeated_requests)
            print(f"Cache hit average time: {cache_avg:.2f}s")
            
            if cache_avg < avg_time:
                print("🎯 Cache is working! Faster response for repeated requests.")
            else:
                print("ℹ️  Cache effect may be minimal (mock mode or similar response times)")
    
    return results

def test_health_endpoint():
    """Test the new health endpoint"""
    print("\n🏥 HEALTH CHECK")
    print("=" * 20)
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print("✅ Health check passed")
            print(f"   Status: {data['status']}")
            print(f"   Mock mode: {data['mock_mode']}")
            print(f"   Cache enabled: {data['cache_enabled']}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")

def test_cache_management():
    """Test cache clearing"""
    print("\n🧹 CACHE MANAGEMENT")
    print("=" * 20)
    
    try:
        response = requests.delete(f"{BASE_URL}/cache")
        if response.status_code == 200:
            data = response.json()
            print("✅ Cache cleared successfully")
            print(f"   {data['message']}")
        else:
            print(f"❌ Cache clear failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Cache clear error: {e}")

if __name__ == "__main__":
    try:
        # Test health first
        test_health_endpoint()
        
        # Run performance tests
        results = test_performance()
        
        # Test cache management
        test_cache_management()
        
        print("\n🎉 EFFICIENCY IMPROVEMENTS DEMONSTRATED!")
        print("✨ Key optimizations implemented:")
        print("   • Model initialization moved to module level")
        print("   • Length configs cached as constants")
        print("   • Environment variables loaded once")
        print("   • In-memory caching for repeated requests")
        print("   • Efficient string processing")
        print("   • Health monitoring endpoints")
        
    except KeyboardInterrupt:
        print("\n⏹️  Testing interrupted by user")
    except Exception as e:
        print(f"\n❌ Testing error: {e}")