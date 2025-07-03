#!/usr/bin/env python3
"""
Test script for GitHub/Vercel webhook deployment integration
"""

import os
import json
import time
import hmac
import hashlib
import requests
from datetime import datetime

# Configuration
WEBHOOK_BASE_URL = os.getenv('WEBHOOK_BASE_URL', 'https://jobportal-connector.vercel.app')
GITHUB_WEBHOOK_SECRET = os.getenv('GITHUB_WEBHOOK_SECRET', 'test-secret-123')
VERCEL_WEBHOOK_SECRET = os.getenv('VERCEL_WEBHOOK_SECRET', 'test-vercel-secret-456')

def create_github_signature(payload: str, secret: str) -> str:
    """Create GitHub webhook signature"""
    signature = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return f"sha256={signature}"

def create_vercel_signature(payload: str, secret: str) -> str:
    """Create Vercel webhook signature"""
    return hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha1
    ).hexdigest()

def test_webhook_endpoints():
    """Test that webhook endpoints are accessible"""
    print("🔄 Testing Webhook Endpoints Accessibility")
    print("-" * 50)
    
    endpoints = [
        "/",
        "/api/health", 
        "/webhooks/github",
        "/webhooks/vercel"
    ]
    
    results = {}
    
    for endpoint in endpoints:
        url = f"{WEBHOOK_BASE_URL}{endpoint}"
        print(f"   Testing: {endpoint}")
        
        try:
            if endpoint in ["/webhooks/github", "/webhooks/vercel"]:
                # Test with GET (should return 405 Method Not Allowed)
                response = requests.get(url, timeout=10)
                if response.status_code == 405:
                    print(f"   ✅ {endpoint} - Endpoint exists (405 Method Not Allowed expected)")
                    results[endpoint] = True
                else:
                    print(f"   ⚠️ {endpoint} - Unexpected status: {response.status_code}")
                    results[endpoint] = False
            else:
                # Test with GET
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    print(f"   ✅ {endpoint} - OK")
                    results[endpoint] = True
                else:
                    print(f"   ❌ {endpoint} - Status: {response.status_code}")
                    results[endpoint] = False
                    
        except Exception as e:
            print(f"   ❌ {endpoint} - Error: {e}")
            results[endpoint] = False
    
    return results

def test_github_push_webhook():
    """Test GitHub push webhook simulation"""
    print("\n🔄 Testing GitHub Push Webhook")
    print("-" * 40)
    
    # Simulate a GitHub push event that would trigger deployment
    test_payload = {
        "ref": "refs/heads/main",
        "before": "0000000000000000000000000000000000000000",
        "after": "abc123def456789012345678901234567890abcd",
        "repository": {
            "id": 123456789,
            "name": "jobportal_connector",
            "full_name": "your-username/jobportal_connector",
            "html_url": "https://github.com/your-username/jobportal_connector",
            "description": "Job portal connector with webhook integration"
        },
        "pusher": {
            "name": "testuser",
            "email": "test@example.com"
        },
        "sender": {
            "login": "testuser",
            "avatar_url": "https://github.com/avatars/testuser"
        },
        "commits": [
            {
                "id": "abc123def456789012345678901234567890abcd",
                "message": "feat: add webhook integration for deployment testing",
                "timestamp": datetime.now().isoformat(),
                "author": {
                    "name": "Test User",
                    "email": "test@example.com"
                },
                "added": ["api/webhooks/handlers.py"],
                "modified": ["api/index.py", "vercel.json"],
                "removed": []
            }
        ]
    }
    
    payload_str = json.dumps(test_payload)
    signature = create_github_signature(payload_str, GITHUB_WEBHOOK_SECRET)
    
    headers = {
        'Content-Type': 'application/json',
        'X-GitHub-Event': 'push',
        'X-Hub-Signature-256': signature,
        'X-GitHub-Delivery': f'test-push-{int(time.time())}',
        'User-Agent': 'GitHub-Hookshot/test'
    }
    
    webhook_url = f"{WEBHOOK_BASE_URL}/webhooks/github"
    print(f"   Sending to: {webhook_url}")
    print(f"   Event: push to main branch")
    print(f"   Commits: {len(test_payload['commits'])}")
    
    try:
        response = requests.post(webhook_url, data=payload_str, headers=headers, timeout=30)
        
        print(f"\n   Response status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ GitHub webhook processed successfully!")
            try:
                response_data = response.json()
                print(f"   Response: {json.dumps(response_data, indent=2)}")
            except:
                print(f"   Response text: {response.text}")
            return True
        else:
            print(f"   ❌ GitHub webhook failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error testing GitHub webhook: {e}")
        return False

def test_vercel_deployment_webhook():
    """Test Vercel deployment webhook simulation"""
    print("\n🔄 Testing Vercel Deployment Webhook")
    print("-" * 45)
    
    # Simulate a Vercel deployment event
    test_payload = {
        "id": f"evt_test_{int(time.time())}",
        "type": "deployment.ready",
        "createdAt": int(time.time() * 1000),
        "data": {
            "deployment": {
                "id": f"dpl_test_{int(time.time())}",
                "url": "jobportal-connector-test.vercel.app",
                "name": "jobportal-connector",
                "target": "production", 
                "state": "READY",
                "type": "PRODUCTION",
                "creator": {
                    "uid": "test-user-id",
                    "username": "testuser",
                    "email": "test@example.com"
                },
                "meta": {
                    "githubCommitSha": "abc123def456789012345678901234567890abcd",
                    "githubCommitMessage": "feat: add webhook integration for deployment testing",
                    "githubCommitAuthorName": "Test User", 
                    "githubCommitRef": "refs/heads/main",
                    "githubRepo": "jobportal_connector"
                },
                "createdAt": int(time.time() * 1000) - 120000,  # 2 minutes ago
                "buildingAt": int(time.time() * 1000) - 60000,  # 1 minute ago  
                "ready": int(time.time() * 1000)  # Now
            },
            "project": {
                "id": "test-project-id",
                "name": "jobportal-connector"
            }
        }
    }
    
    payload_str = json.dumps(test_payload)
    signature = create_vercel_signature(payload_str, VERCEL_WEBHOOK_SECRET)
    
    headers = {
        'Content-Type': 'application/json',
        'X-Vercel-Signature': signature,
        'User-Agent': 'Vercel/1.0'
    }
    
    webhook_url = f"{WEBHOOK_BASE_URL}/webhooks/vercel"
    print(f"   Sending to: {webhook_url}")
    print(f"   Event: {test_payload['type']}")
    print(f"   Deployment state: {test_payload['data']['deployment']['state']}")
    print(f"   Project: {test_payload['data']['project']['name']}")
    
    try:
        response = requests.post(webhook_url, data=payload_str, headers=headers, timeout=30)
        
        print(f"\n   Response status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ Vercel webhook processed successfully!")
            try:
                response_data = response.json()
                print(f"   Response: {json.dumps(response_data, indent=2)}")
            except:
                print(f"   Response text: {response.text}")
            return True
        else:
            print(f"   ❌ Vercel webhook failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error testing Vercel webhook: {e}")
        return False

def test_deployment_flow():
    """Test the complete deployment flow"""
    print("\n🔄 Testing Complete Deployment Flow")
    print("-" * 45)
    
    print("   Simulating deployment sequence:")
    print("   1. GitHub push → triggers Vercel deployment")
    print("   2. Vercel starts building")
    print("   3. Vercel deployment completes")
    
    # Test the sequence
    github_success = test_github_push_webhook()
    time.sleep(2)  # Simulate build time
    vercel_success = test_vercel_deployment_webhook()
    
    if github_success and vercel_success:
        print("\n   ✅ Complete deployment flow tested successfully!")
        return True
    else:
        print("\n   ❌ Deployment flow test failed")
        return False

def check_deployment_status():
    """Check if the current deployment is accessible"""
    print("\n🔄 Checking Current Deployment Status")
    print("-" * 45)
    
    try:
        health_url = f"{WEBHOOK_BASE_URL}/api/health"
        response = requests.get(health_url, timeout=10)
        
        if response.status_code == 200:
            health_data = response.json()
            print(f"   ✅ Deployment is live and healthy!")
            print(f"   Status: {health_data.get('status', 'unknown')}")
            print(f"   Service: {health_data.get('service', 'unknown')}")
            
            # Check root endpoint for webhook info
            root_response = requests.get(WEBHOOK_BASE_URL, timeout=10)
            if root_response.status_code == 200:
                root_data = root_response.json()
                endpoints = root_data.get('endpoints', {})
                print(f"   Available endpoints: {list(endpoints.keys())}")
            
            return True
        else:
            print(f"   ❌ Deployment health check failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error checking deployment: {e}")
        return False

def main():
    """Run the complete webhook deployment test suite"""
    print("🚀 Webhook Deployment Test Suite")
    print("=" * 60)
    print(f"Target URL: {WEBHOOK_BASE_URL}")
    print("=" * 60)
    
    # Test current deployment status
    deployment_ok = check_deployment_status()
    
    # Test webhook endpoints
    endpoints_ok = test_webhook_endpoints()
    endpoints_success = all(endpoints_ok.values())
    
    # Test webhook functionality
    github_ok = test_github_push_webhook()
    vercel_ok = test_vercel_deployment_webhook()
    
    # Test complete flow
    flow_ok = test_deployment_flow()
    
    # Summary
    print("\n" + "=" * 60)
    print("🎉 Test Summary")
    print("-" * 30)
    print(f"✅ Deployment Status: {'OK' if deployment_ok else 'FAILED'}")
    print(f"✅ Webhook Endpoints: {'OK' if endpoints_success else 'FAILED'}")
    print(f"✅ GitHub Webhook: {'OK' if github_ok else 'FAILED'}")
    print(f"✅ Vercel Webhook: {'OK' if vercel_ok else 'FAILED'}")
    print(f"✅ Complete Flow: {'OK' if flow_ok else 'FAILED'}")
    
    all_passed = all([deployment_ok, endpoints_success, github_ok, vercel_ok, flow_ok])
    
    if all_passed:
        print("\n🎉 All tests passed! Webhook deployment integration is working!")
        print("\nYour setup:")
        print(f"- GitHub webhook → {WEBHOOK_BASE_URL}/webhooks/github")
        print(f"- Vercel webhook → {WEBHOOK_BASE_URL}/webhooks/vercel")
        print("\nTo trigger a real deployment:")
        print("1. Make a commit to your main branch")
        print("2. Push to GitHub")
        print("3. GitHub webhook will trigger Vercel deployment")
        print("4. Vercel will send deployment status webhooks")
    else:
        print("\n⚠️ Some tests failed. Check the configuration above.")
        
        if not deployment_ok:
            print("\n🔧 Deployment Issues:")
            print("- Make sure your Vercel deployment is live")
            print("- Check the URL is correct")
            
        if not endpoints_success:
            print("\n🔧 Endpoint Issues:")
            print("- Webhook endpoints may not be deployed")
            print("- Check the API routing configuration")

if __name__ == "__main__":
    main()
