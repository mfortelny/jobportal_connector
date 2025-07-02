#!/usr/bin/env python3
"""
Webhook Integration Test Script
Tests both incoming and outgoing webhook functionality
"""

import os
import json
import time
import hmac
import hashlib
import requests
from datetime import datetime
from supabase import create_client, Client

# Configuration
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://your-project-ref.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY', 'your-service-role-key')
GITHUB_WEBHOOK_SECRET = os.getenv('GITHUB_WEBHOOK_SECRET', 'your-webhook-secret')
WEBHOOK_ENDPOINT = f"{SUPABASE_URL}/functions/v1/github-webhook"

# Initialize Supabase client
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Supabase client initialized")
except Exception as e:
    print(f"❌ Failed to initialize Supabase client: {e}")
    exit(1)

def create_github_signature(payload: str, secret: str) -> str:
    """Create GitHub webhook signature"""
    signature = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return f"sha256={signature}"

def test_incoming_webhook():
    """Test incoming webhook from GitHub to Supabase"""
    print("\n🔄 Testing Incoming Webhook (GitHub → Supabase)")
    
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
                "id": "abc123",
                "message": "Test commit from webhook integration test",
                "author": {
                    "name": "Test User",
                    "email": "test@example.com"
                },
                "url": "https://github.com/test-user/test-repo/commit/abc123"
            }
        ]
    }
    
    payload_str = json.dumps(test_payload)
    signature = create_github_signature(payload_str, GITHUB_WEBHOOK_SECRET)
    
    headers = {
        'Content-Type': 'application/json',
        'X-GitHub-Event': 'push',
        'X-Hub-Signature-256': signature,
        'User-Agent': 'GitHub-Hookshot/test'
    }
    
    try:
        response = requests.post(WEBHOOK_ENDPOINT, data=payload_str, headers=headers, timeout=30)
        
        if response.status_code == 200:
            print("✅ Webhook request successful")
            print(f"   Response: {response.json()}")
            
            # Wait a moment for processing
            time.sleep(2)
            
            # Check if webhook was logged
            result = supabase.table('github_webhook_logs')\
                .select('*')\
                .eq('event_type', 'push')\
                .eq('repository_name', 'test-user/test-repo')\
                .order('created_at', desc=True)\
                .limit(1)\
                .execute()
            
            if result.data:
                print("✅ Webhook logged in database")
                print(f"   Log ID: {result.data[0]['id']}")
            else:
                print("⚠️ Webhook not found in logs table")
            
            # Check if commit was stored
            commit_result = supabase.table('github_commits')\
                .select('*')\
                .eq('commit_sha', 'abc123')\
                .limit(1)\
                .execute()
            
            if commit_result.data:
                print("✅ Commit stored in database")
                print(f"   Commit: {commit_result.data[0]['message']}")
            else:
                print("⚠️ Commit not found in commits table")
                
        else:
            print(f"❌ Webhook request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing incoming webhook: {e}")

def test_outgoing_webhook():
    """Test outgoing webhook from Supabase to external service"""
    print("\n🔄 Testing Outgoing Webhook (Supabase → External)")
    
    try:
        # First, ensure we have a company and position
        company_result = supabase.table('companies')\
            .insert({'name': 'Test Webhook Company'})\
            .execute()
        
        if not company_result.data:
            print("❌ Failed to create test company")
            return
            
        company_id = company_result.data[0]['id']
        print(f"✅ Created test company: {company_id}")
        
        position_result = supabase.table('positions')\
            .insert({
                'company_id': company_id,
                'title': 'Test Webhook Position'
            })\
            .execute()
        
        if not position_result.data:
            print("❌ Failed to create test position")
            return
            
        position_id = position_result.data[0]['id']
        print(f"✅ Created test position: {position_id}")
        
        # Now insert a candidate to trigger the webhook
        candidate_result = supabase.table('candidates')\
            .insert({
                'position_id': position_id,
                'first_name': 'Webhook',
                'last_name': 'Test',
                'email': 'webhook-test@example.com',
                'phone': '+1-555-WEBHOOK',
                'source_url': 'https://test-webhook-integration.com'
            })\
            .execute()
        
        if candidate_result.data:
            candidate_id = candidate_result.data[0]['id']
            print(f"✅ Created test candidate: {candidate_id}")
            
            # Wait for webhook to process
            time.sleep(5)
            
            # Check if webhook call was logged
            api_calls = supabase.table('github_api_calls')\
                .select('*')\
                .eq('triggered_by_table', 'candidates')\
                .eq('triggered_by_id', candidate_id)\
                .execute()
            
            if api_calls.data:
                print("✅ Outgoing webhook logged")
                for call in api_calls.data:
                    print(f"   Endpoint: {call['endpoint']}")
                    print(f"   Status: {call.get('response_status', 'Pending')}")
            else:
                print("⚠️ No outgoing webhook calls found")
                
        else:
            print("❌ Failed to create test candidate")
            
    except Exception as e:
        print(f"❌ Error testing outgoing webhook: {e}")

def test_database_connectivity():
    """Test basic database connectivity and required tables"""
    print("\n🔄 Testing Database Connectivity")
    
    required_tables = [
        'github_webhook_logs',
        'github_commits', 
        'github_pull_requests',
        'github_issues',
        'github_repositories',
        'github_api_calls',
        'companies',
        'positions',
        'candidates'
    ]
    
    for table in required_tables:
        try:
            result = supabase.table(table).select('id').limit(1).execute()
            print(f"✅ Table '{table}' accessible")
        except Exception as e:
            print(f"❌ Table '{table}' error: {e}")

def test_edge_function_deployment():
    """Test if the Edge Function is deployed and accessible"""
    print("\n🔄 Testing Edge Function Deployment")
    
    try:
        # Test with a simple GET request (should return 405 Method Not Allowed)
        response = requests.get(WEBHOOK_ENDPOINT, timeout=10)
        
        if response.status_code == 405:
            print("✅ Edge Function is deployed and accessible")
        elif response.status_code == 404:
            print("❌ Edge Function not found - check deployment")
        else:
            print(f"⚠️ Unexpected response from Edge Function: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot reach Edge Function: {e}")

def check_configuration():
    """Check if required configuration is set"""
    print("\n🔄 Checking Configuration")
    
    config_items = [
        ('SUPABASE_URL', SUPABASE_URL),
        ('SUPABASE_SERVICE_ROLE_KEY', SUPABASE_KEY),
        ('GITHUB_WEBHOOK_SECRET', GITHUB_WEBHOOK_SECRET)
    ]
    
    for name, value in config_items:
        if value and not value.startswith('your-'):
            print(f"✅ {name} configured")
        else:
            print(f"❌ {name} not properly configured")

def main():
    """Run all tests"""
    print("🪝 Webhook Integration Test Suite")
    print("=" * 50)
    
    check_configuration()
    test_database_connectivity()
    test_edge_function_deployment()
    test_incoming_webhook()
    test_outgoing_webhook()
    
    print("\n" + "=" * 50)
    print("🎉 Test suite completed!")
    print("\nNext steps:")
    print("1. Check the webhook logs in your Supabase dashboard")
    print("2. Verify GitHub webhook is configured in your repository")
    print("3. Test with real GitHub events (create an issue, make a push)")
    print("4. Monitor the github_api_calls table for outbound webhooks")

if __name__ == "__main__":
    main() 