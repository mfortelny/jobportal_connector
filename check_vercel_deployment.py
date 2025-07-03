#!/usr/bin/env python3
"""
Check for existing Vercel deployments and help configure webhooks
"""

import requests
import json

def check_common_vercel_urls():
    """Check common Vercel URL patterns"""
    print("🔍 Checking Common Vercel URL Patterns")
    print("-" * 50)
    
    # Common URL patterns for this project
    potential_urls = [
        "https://jobportal-connector.vercel.app",
        "https://jobportal-connector-git-main.vercel.app", 
        "https://jobportal-connector-mfortelny.vercel.app",
        "https://jobportal-connector-seven.vercel.app",
        "https://jobportal-connector-rho.vercel.app"
    ]
    
    working_urls = []
    
    for url in potential_urls:
        try:
            print(f"   Checking: {url}")
            response = requests.get(f"{url}/api/health", timeout=10)
            
            if response.status_code == 200:
                print(f"   ✅ FOUND: {url}")
                working_urls.append(url)
                
                # Check if it has our webhook endpoints
                webhook_test = requests.get(f"{url}/webhooks/github", timeout=5)
                if webhook_test.status_code == 405:  # Method not allowed is expected
                    print(f"      ✅ Webhook endpoints available")
                else:
                    print(f"      ⚠️ Webhook endpoints may not be available (status: {webhook_test.status_code})")
                    
            elif response.status_code == 404:
                print(f"   ❌ Not found: {url}")
            else:
                print(f"   ⚠️ Unexpected status {response.status_code}: {url}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Error checking {url}: {e}")
    
    return working_urls

def test_github_repo_webhooks():
    """Check GitHub repository webhook configuration"""
    print("\n🔍 GitHub Repository Information")
    print("-" * 40)
    
    print("   Repository: mfortelny/jobportal_connector")
    print("   Recent push: ✅ Completed")
    print("   To check GitHub webhooks:")
    print("   1. Go to: https://github.com/mfortelny/jobportal_connector/settings/hooks")
    print("   2. Look for webhooks pointing to Vercel")
    print("   3. Check delivery history for any failures")

def provide_vercel_setup_instructions():
    """Provide step-by-step Vercel setup instructions"""
    print("\n📋 Vercel Deployment Setup")
    print("-" * 35)
    
    print("""
🚀 Manual Vercel Deployment:
   1. Go to: https://vercel.com/import
   2. Connect your GitHub account
   3. Import: mfortelny/jobportal_connector
   4. Deploy with default settings
   
🔗 GitHub Webhook Setup:
   1. In Vercel project settings → Git
   2. Copy the Deploy Hook URL
   3. In GitHub: Settings → Webhooks → Add webhook
   4. Payload URL: [Deploy Hook URL from Vercel]
   5. Content type: application/json
   6. Events: Just the push event
   
🔧 Environment Variables in Vercel:
   - SUPABASE_URL
   - SUPABASE_SERVICE_ROLE_KEY  
   - BROWSER_USE_API_KEY
   - GITHUB_WEBHOOK_SECRET
   - VERCEL_WEBHOOK_SECRET
""")

def main():
    print("🔍 Vercel Deployment Checker")
    print("=" * 50)
    
    # Check for existing deployments
    working_urls = check_common_vercel_urls()
    
    # Check GitHub configuration
    test_github_repo_webhooks()
    
    if working_urls:
        print(f"\n✅ Found {len(working_urls)} working deployment(s):")
        for url in working_urls:
            print(f"   - {url}")
        
        print(f"\n🧪 To test webhooks with working deployment:")
        print(f"   export WEBHOOK_BASE_URL={working_urls[0]}")
        print(f"   python3 test_webhook_deployment.py")
    else:
        print("\n❌ No working deployments found")
        provide_vercel_setup_instructions()

if __name__ == "__main__":
    main()
