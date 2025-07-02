#!/bin/bash

# Webhook Integration Deployment Script
# This script automates the deployment of GitHub webhook integration

set -e  # Exit on any error

echo "🪝 Deploying Webhook Integration..."
echo "=================================="

# Check if Supabase CLI is installed
if ! command -v supabase &> /dev/null; then
    echo "❌ Supabase CLI not found. Please install it first:"
    echo "   npm install -g supabase"
    exit 1
fi

# Check if we're in a Supabase project
if [ ! -f "supabase/config.toml" ]; then
    echo "❌ Not in a Supabase project directory"
    echo "   Run this script from your project root"
    exit 1
fi

echo "✅ Supabase CLI found"

# Check if logged in
if ! supabase projects list &> /dev/null; then
    echo "❌ Not logged in to Supabase"
    echo "   Run: supabase login"
    exit 1
fi

echo "✅ Supabase authentication verified"

# Step 1: Deploy database migrations
echo ""
echo "📊 Deploying database schema..."
if supabase db push; then
    echo "✅ Database migrations applied successfully"
else
    echo "❌ Failed to apply database migrations"
    exit 1
fi

# Step 2: Deploy Edge Function
echo ""
echo "⚡ Deploying Edge Function..."
if supabase functions deploy github-webhook --no-verify-jwt; then
    echo "✅ Edge Function deployed successfully"
else
    echo "❌ Failed to deploy Edge Function"
    exit 1
fi

# Step 3: Get project details
echo ""
echo "📋 Getting project information..."
PROJECT_REF=$(supabase status | grep "API URL" | cut -d'/' -f3 | cut -d'.' -f1)
if [ -z "$PROJECT_REF" ]; then
    PROJECT_REF=$(supabase projects list --output json | jq -r '.[0].id' 2>/dev/null || echo "")
fi

if [ -z "$PROJECT_REF" ]; then
    echo "⚠️ Could not automatically detect project reference"
    echo "   Please check your project URL manually"
    PROJECT_REF="your-project-ref"
fi

echo "   Project Reference: $PROJECT_REF"

# Step 4: Show next steps
echo ""
echo "🎉 Deployment completed successfully!"
echo ""
echo "📝 Next Steps:"
echo "=============="
echo ""
echo "1. 🔐 Set up secrets:"
echo "   supabase secrets set GITHUB_WEBHOOK_SECRET=your_webhook_secret_here"
echo "   supabase secrets set GITHUB_TOKEN=github_pat_your_token_here"
echo ""
echo "2. 🔗 Configure GitHub webhook:"
echo "   URL: https://${PROJECT_REF}.supabase.co/functions/v1/github-webhook"
echo "   Content-Type: application/json"
echo "   Events: push, pull_request, issues"
echo "   Secret: (use the same secret from step 1)"
echo ""
echo "3. 🧪 Test the integration:"
echo "   python3 test_webhook_integration.py"
echo ""
echo "4. 📖 Read the full setup guide:"
echo "   cat WEBHOOK_INTEGRATION_SETUP.md"

# Step 5: Check for required environment variables
echo ""
echo "🔧 Environment Check:"
echo "====================="

if [ -z "$SUPABASE_URL" ]; then
    echo "⚠️  Set SUPABASE_URL environment variable"
    echo "   export SUPABASE_URL=https://${PROJECT_REF}.supabase.co"
fi

if [ -z "$SUPABASE_SERVICE_ROLE_KEY" ]; then
    echo "⚠️  Set SUPABASE_SERVICE_ROLE_KEY environment variable"
    echo "   Get it from: https://supabase.com/dashboard/project/${PROJECT_REF}/settings/api"
fi

if [ -z "$GITHUB_WEBHOOK_SECRET" ]; then
    echo "⚠️  Set GITHUB_WEBHOOK_SECRET environment variable"
    echo "   Generate a strong secret for webhook verification"
fi

# Step 6: Show useful commands
echo ""
echo "🛠️  Useful Commands:"
echo "==================="
echo "View Edge Function logs:    supabase functions logs github-webhook"
echo "Check webhook logs:         supabase db reset && supabase db push"
echo "Test database connection:   python3 -c \"from test_webhook_integration import test_database_connectivity; test_database_connectivity()\""
echo ""
echo "🔗 Helpful Links:"
echo "=================="
echo "Supabase Dashboard:         https://supabase.com/dashboard/project/${PROJECT_REF}"
echo "Edge Functions:             https://supabase.com/dashboard/project/${PROJECT_REF}/functions"
echo "Database:                   https://supabase.com/dashboard/project/${PROJECT_REF}/editor"
echo "GitHub Token Settings:      https://github.com/settings/tokens"
echo ""
echo "Happy webhooking! 🪝✨" 