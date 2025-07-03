#!/usr/bin/env python3
"""
Simple Webhook Integration Test Script
Tests webhook functionality without complex dependencies
"""

import os
import json
import time
import hmac
import hashlib
import sys

try:
    import requests
except ImportError:
    print("❌ requests library not available. Installing...")
    os.system("pip install requests")
    import requests

# Configuration from environment variables
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://your-project-ref.supabase.co')
GITHUB_WEBHOOK_SECRET = os.getenv('GITHUB_WEBHOOK_SECRET', 'your-webhook-secret')
WEBHOOK_ENDPOINT = f"{SUPABASE_URL}/functions/v1/github-webhook"

def create_github_signature(payload: str, secret: str) -> str:
    """Create GitHub webhook signature"""
    signature = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return f"sha256={signature}"

def test_edge_function_deployment():
    """Test if the Edge Function is deployed and accessible"""
    print("🔄 Testing Edge Function Deployment")
    print("-" * 40)
    
    try:
        # Test with a simple GET request (should return 405 Method Not Allowed)
        response = requests.get(WEBHOOK_ENDPOINT, timeout=10)
        
        if response.status_code == 405:
            print("✅ Edge Function is deployed and accessible")
            print(f"   Response: {response.status_code} - Method Not Allowed (expected)")
            return True
        elif response.status_code == 404:
            print("❌ Edge Function not found - check deployment")
            print("   Run: supabase functions deploy github-webhook --no-verify-jwt")
            return False
        else:
            print(f"⚠️ Unexpected response from Edge Function: {response.status_code}")
            print(f"   Response text: {response.text[:200]}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot reach Edge Function: {e}")
        print("   Check if Supabase URL is correct and function is deployed")
        return False

def test_incoming_webhook():
    """Test incoming webhook from GitHub to Supabase"""
    print("\n🔄 Testing Incoming Webhook (GitHub → Supabase)")
    print("-" * 50)
    
    # Sample GitHub push event payload
    test_payload = {
        "ref": "refs/heads/main",
        "repository": {
            "name": "test-repo",
            "full_name": "test-user/test-repo",
            "html_url": "https://github.com/test-user/test-repo"
        },
        "sender": {
            "login": "test-user",
            "avatar_url": "https://github.com/avatars/test-user"
        },
        "commits": [
            {
                "id": "abc123def456",
                "message": "Test commit from webhook integration test",
                "author": {
                    "name": "Test User",
                    "email": "test@example.com"
                },
                "url": "https://github.com/test-user/test-repo/commit/abc123def456"
            }
        ]
    }
    
    payload_str = json.dumps(test_payload)
    signature = create_github_signature(payload_str, GITHUB_WEBHOOK_SECRET)
    
    headers = {
        'Content-Type': 'application/json',
        'X-GitHub-Event': 'push',
        'X-Hub-Signature-256': signature,
        'User-Agent': 'GitHub-Hookshot/test',
        'X-GitHub-Delivery': 'test-' + str(int(time.time()))
    }
    
    print(f"   Sending webhook to: {WEBHOOK_ENDPOINT}")
    print(f"   Event type: push")
    print(f"   Repository: test-user/test-repo")
    print(f"   Commits: 1")
    
    try:
        response = requests.post(WEBHOOK_ENDPOINT, data=payload_str, headers=headers, timeout=30)
        
        print(f"\n   Response status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Webhook request successful!")
            try:
                response_data = response.json()
                print(f"   Response data: {json.dumps(response_data, indent=2)}")
            except:
                print(f"   Response text: {response.text}")
            return True
        elif response.status_code == 401:
            print("❌ Webhook signature verification failed")
            print("   Check that GITHUB_WEBHOOK_SECRET matches the secret used in your Edge Function")
            return False
        else:
            print(f"❌ Webhook request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing incoming webhook: {e}")
        return False

def test_webhook_with_different_events():
    """Test webhook with different GitHub event types"""
    print("\n🔄 Testing Different GitHub Event Types")
    print("-" * 45)
    
    events = [
        {
            "event_type": "issues",
            "payload": {
                "action": "opened",
                "issue": {
                    "number": 42,
                    "title": "Test Issue from Webhook Integration",
                    "html_url": "https://github.com/test-user/test-repo/issues/42",
                    "state": "open",
                    "user": {
                        "login": "test-user"
                    }
                },
                "repository": {
                    "name": "test-repo",
                    "full_name": "test-user/test-repo",
                    "html_url": "https://github.com/test-user/test-repo"
                },
                "sender": {
                    "login": "test-user"
                }
            }
        },
        {
            "event_type": "pull_request",
            "payload": {
                "action": "opened",
                "pull_request": {
                    "number": 123,
                    "title": "Test PR from Webhook Integration",
                    "html_url": "https://github.com/test-user/test-repo/pull/123",
                    "state": "open",
                    "user": {
                        "login": "test-user"
                    }
                },
                "repository": {
                    "name": "test-repo",
                    "full_name": "test-user/test-repo",
                    "html_url": "https://github.com/test-user/test-repo"
                },
                "sender": {
                    "login": "test-user"
                }
            }
        }
    ]
    
    success_count = 0
    
    for event in events:
        print(f"\n   Testing {event['event_type']} event...")
        
        payload_str = json.dumps(event["payload"])
        signature = create_github_signature(payload_str, GITHUB_WEBHOOK_SECRET)
        
        headers = {
            'Content-Type': 'application/json',
            'X-GitHub-Event': event["event_type"],
            'X-Hub-Signature-256': signature,
            'User-Agent': 'GitHub-Hookshot/test',
            'X-GitHub-Delivery': f'test-{event["event_type"]}-{int(time.time())}'
        }
        
        try:
            response = requests.post(WEBHOOK_ENDPOINT, data=payload_str, headers=headers, timeout=30)
            
            if response.status_code == 200:
                print(f"   ✅ {event['event_type']} event processed successfully")
                success_count += 1
            else:
                print(f"   ❌ {event['event_type']} event failed: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ {event['event_type']} event error: {e}")
    
    print(f"\n   Summary: {success_count}/{len(events)} events processed successfully")
    return success_count == len(events)

def check_configuration():
    """Check if required configuration is set"""
    print("🔄 Checking Configuration")
    print("-" * 30)
    
    issues = []
    
    if SUPABASE_URL == 'https://your-project-ref.supabase.co':
        issues.append("SUPABASE_URL not configured")
        print("❌ SUPABASE_URL not configured")
        print("   Set with: export SUPABASE_URL=https://your-actual-project-ref.supabase.co")
    else:
        print("✅ SUPABASE_URL configured")
        print(f"   URL: {SUPABASE_URL}")
    
    if GITHUB_WEBHOOK_SECRET == 'your-webhook-secret':
        issues.append("GITHUB_WEBHOOK_SECRET not configured")
        print("❌ GITHUB_WEBHOOK_SECRET not configured")
        print("   Set with: export GITHUB_WEBHOOK_SECRET=your_actual_webhook_secret")
    else:
        print("✅ GITHUB_WEBHOOK_SECRET configured")
        print("   Secret: " + "*" * min(len(GITHUB_WEBHOOK_SECRET), 20) + "...")
    
    if issues:
        print(f"\n⚠️ Configuration issues found: {len(issues)}")
        return False
    else:
        print("\n✅ All configuration looks good!")
        return True

def show_setup_instructions():
    """Show setup instructions for webhook integration"""
    print("\n📋 Setup Instructions")
    print("=" * 50)
    
    print(f"""
1. 🚀 Deploy the Edge Function:
   supabase functions deploy github-webhook --no-verify-jwt

2. 🔐 Set up Supabase secrets:
   supabase secrets set GITHUB_WEBHOOK_SECRET=your_webhook_secret_here
   supabase secrets set GITHUB_TOKEN=github_pat_your_token_here

3. 🔗 Configure GitHub webhook in your repository:
   URL: {WEBHOOK_ENDPOINT}
   Content-Type: application/json
   Events: push, pull_request, issues
   Secret: (same as GITHUB_WEBHOOK_SECRET above)

4. 🧪 Set environment variables for testing:
   export SUPABASE_URL={SUPABASE_URL}
   export GITHUB_WEBHOOK_SECRET=your_webhook_secret_here

5. 📊 Apply database migrations:
   supabase db push
""")

def main():
    """Run webhook tests"""
    print("🪝 Simple Webhook Integration Test")
    print("=" * 50)
    
    # Check configuration
    config_ok = check_configuration()
    
    if not config_ok:
        show_setup_instructions()
        print("\n❌ Please fix configuration issues before testing")
        return False
    
    # Test deployment
    deployment_ok = test_edge_function_deployment()
    
    if not deployment_ok:
        print("\n❌ Edge Function not accessible. Please deploy first.")
        show_setup_instructions()
        return False
    
    # Test basic webhook
    webhook_ok = test_incoming_webhook()
    
    # Test different event types
    events_ok = test_webhook_with_different_events()
    
    # Summary
    print("\n" + "=" * 50)
    print("🎉 Test Summary")
    print("-" * 20)
    print(f"✅ Configuration: {'OK' if config_ok else 'FAILED'}")
    print(f"✅ Edge Function: {'OK' if deployment_ok else 'FAILED'}")
    print(f"✅ Basic Webhook: {'OK' if webhook_ok else 'FAILED'}")
    print(f"✅ Event Types: {'OK' if events_ok else 'FAILED'}")
    
    if all([config_ok, deployment_ok, webhook_ok, events_ok]):
        print("\n🎉 All tests passed! Webhook integration is working!")
        print("\nNext steps:")
        print("- Configure the webhook URL in your GitHub repository")
        print("- Test with real GitHub events")
        print("- Monitor webhook logs in Supabase dashboard")
    else:
        print("\n⚠️ Some tests failed. Check the issues above.")
    
    return all([config_ok, deployment_ok, webhook_ok, events_ok])

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 