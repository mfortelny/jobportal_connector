#!/usr/bin/env python3
"""
Test live deployment webhook integration
"""

import requests
import json

def test_deployment_endpoints():
    """Test if deployment is live and has webhook endpoints"""
    
    # You'll need to replace this with your actual Vercel URL after deployment
    base_url = input("Enter your Vercel deployment URL (e.g., https://jobportal-connector-abc123.vercel.app): ").strip()
    
    if not base_url:
        print("❌ No URL provided")
        return False
        
    print(f"\n🔄 Testing: {base_url}")
    print("-" * 50)
    
    endpoints = [
        "/",
        "/api/health",
        "/webhooks/github", 
        "/webhooks/vercel"
    ]
    
    results = {}
    
    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        try:
            if endpoint.startswith("/webhooks/"):
                # Test with GET (should return 405)
                response = requests.get(url, timeout=10)
                if response.status_code == 405:
                    print(f"✅ {endpoint} - Available (405 Method Not Allowed expected)")
                    results[endpoint] = True
                else:
                    print(f"❌ {endpoint} - Status: {response.status_code}")
                    results[endpoint] = False
            else:
                # Test with GET
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    print(f"✅ {endpoint} - OK")
                    if endpoint == "/":
                        data = response.json()
                        endpoints_list = data.get('endpoints', {})
                        print(f"   Available endpoints: {list(endpoints_list.keys())}")
                    results[endpoint] = True
                else:
                    print(f"❌ {endpoint} - Status: {response.status_code}")
                    results[endpoint] = False
                    
        except Exception as e:
            print(f"❌ {endpoint} - Error: {e}")
            results[endpoint] = False
    
    success_count = sum(results.values())
    total_count = len(results)
    
    print(f"\n🎉 Results: {success_count}/{total_count} endpoints working")
    
    if success_count == total_count:
        print("✅ All endpoints are working!")
        print(f"\n📝 Update your webhook URLs:")
        print(f"   GitHub webhook: {base_url}/webhooks/github")
        print(f"   Vercel webhook: {base_url}/webhooks/vercel")
        return True
    else:
        print("⚠️ Some endpoints failed")
        return False

if __name__ == "__main__":
    test_deployment_endpoints()
