# 🪝 Webhook Integration Setup Guide

This guide shows you how to set up bidirectional webhook integration between Supabase and GitHub.

## 🎯 **Integration Overview**

### **Incoming Webhooks (GitHub → Supabase)**
- GitHub events (pushes, PRs, issues) trigger Supabase Edge Functions
- Events are stored in database tables for analysis
- Secure signature verification included

### **Outgoing Webhooks (Supabase → GitHub)**
- Database changes trigger GitHub API calls
- Automatic GitHub issue creation for new candidates
- Database webhook notifications to external services

### **Available Webhook Types**
1. **GitHub Webhook Handler** - Receives GitHub events
2. **Database Triggers** - Send data changes to GitHub
3. **Manual Webhooks** - Call GitHub API programmatically

---

## 🚀 **Setup Instructions**

### **Step 1: Deploy the Database Schema**

Run the new migrations to create webhook tables:

```bash
# Apply the new schema
supabase db push

# Verify tables were created
supabase db reset  # If needed for fresh start
```

### **Step 2: Deploy the Edge Function**

```bash
# Deploy the GitHub webhook handler
supabase functions deploy github-webhook --no-verify-jwt

# Check deployment status
supabase functions list
```

### **Step 3: Configure GitHub Repository Webhooks**

1. **Go to your GitHub repository settings**
   ```
   https://github.com/your-username/your-repo/settings/hooks
   ```

2. **Add a new webhook with these settings:**
   - **Payload URL**: `https://your-project-ref.supabase.co/functions/v1/github-webhook`
   - **Content type**: `application/json`
   - **Secret**: Generate a strong secret and save it
   - **Events**: Select the events you want to track:
     - ✅ Push events
     - ✅ Pull requests
     - ✅ Issues
     - ✅ Repository (optional)

3. **Test the webhook** by creating a test issue or push

### **Step 4: Configure Environment Variables**

Set the required secrets in Supabase:

```bash
# Set GitHub webhook secret (used for signature verification)
supabase secrets set GITHUB_WEBHOOK_SECRET=your_webhook_secret_here

# Set GitHub Personal Access Token (for outbound API calls)
supabase secrets set GITHUB_TOKEN=github_pat_your_token_here
```

**To get a GitHub Personal Access Token:**
1. Go to: https://github.com/settings/tokens
2. Generate a new token with these permissions:
   - `repo` (full repository access)
   - `issues` (read/write issues)
   - `admin:repo_hook` (manage webhooks)

### **Step 5: Update Configuration in Database Functions**

Update the hardcoded values in your database functions:

```sql
-- Update the GitHub repository and token in triggers
UPDATE pg_proc 
SET prosrc = replace(prosrc, 'your-username/your-repo', 'actual-username/actual-repo')
WHERE proname IN ('notify_github_new_candidate', 'notify_github_scraping_completed');

UPDATE pg_proc 
SET prosrc = replace(prosrc, 'your-project-ref.supabase.co', 'actual-project-ref.supabase.co')
WHERE proname = 'setup_github_repository_webhook';
```

**Or manually edit the functions via SQL:**

```sql
-- Update GitHub repository references
CREATE OR REPLACE FUNCTION notify_github_new_candidate()
-- ... (copy the function and update the hardcoded values)
```

---

## 🧪 **Testing the Integration**

### **Test 1: Incoming Webhooks (GitHub → Supabase)**

1. **Create a test issue in GitHub**
2. **Check Supabase logs:**
   ```sql
   SELECT * FROM github_webhook_logs 
   ORDER BY created_at DESC LIMIT 5;
   ```
3. **Verify issue data:**
   ```sql
   SELECT * FROM github_issues 
   ORDER BY updated_at DESC LIMIT 5;
   ```

### **Test 2: Outgoing Webhooks (Supabase → GitHub)**

1. **Insert a test candidate:**
   ```sql
   INSERT INTO candidates (position_id, first_name, last_name, email, phone)
   VALUES (1, 'John', 'Doe', 'john@example.com', '+1234567890');
   ```

2. **Check if GitHub issue was created** in your repository

3. **Check webhook logs:**
   ```sql
   SELECT * FROM github_api_calls 
   ORDER BY created_at DESC LIMIT 5;
   ```

### **Test 3: Database Webhooks**

1. **Create/update a company:**
   ```sql
   INSERT INTO companies (name) VALUES ('Test Company');
   ```

2. **Check webhook was sent:**
   ```sql
   SELECT * FROM github_api_calls 
   WHERE triggered_by_table = 'companies'
   ORDER BY created_at DESC;
   ```

---

## 🔧 **Configuration Options**

### **Webhook Events You Can Handle**

The Edge Function handles these GitHub events:
- `push` - Code pushes
- `pull_request` - PR created/updated/closed
- `issues` - Issues created/updated/closed
- `repository` - Repository events

### **Database Tables for Webhook Data**

| Table | Purpose |
|-------|---------|
| `github_webhook_logs` | All incoming webhook events |
| `github_commits` | Commit information from pushes |
| `github_pull_requests` | Pull request data |
| `github_issues` | Issue tracking |
| `github_repositories` | Repository metadata |
| `github_api_calls` | Outbound API call logs |

### **Customizing Webhook Responses**

Edit the Edge Function to customize how you handle events:

```typescript
// In supabase/functions/github-webhook/index.ts

async function handlePushEvent(supabase: any, payload: GitHubWebhookEvent) {
  // Your custom logic here
  console.log('Custom push handling:', payload.repository?.full_name)
  
  // Example: Trigger deployment, send notifications, etc.
}
```

---

## 🔐 **Security Considerations**

### **Webhook Signature Verification**
- Always verify GitHub webhook signatures
- Use strong, unique webhook secrets
- Rotate secrets regularly

### **API Token Security**
- Use minimal required permissions for GitHub tokens
- Store tokens in Supabase Vault/Secrets
- Monitor token usage

### **Database Security**
- RLS policies are enabled on all webhook tables
- Service role has full access for Edge Functions
- Authenticated users have read-only access

---

## 📊 **Monitoring and Debugging**

### **Check Edge Function Logs**
```bash
supabase functions logs github-webhook
```

### **Monitor Webhook Performance**
```sql
-- Webhook success rate
SELECT 
  endpoint,
  COUNT(*) as total_calls,
  COUNT(CASE WHEN response_status >= 200 AND response_status < 300 THEN 1 END) as successful,
  AVG(EXTRACT(EPOCH FROM (created_at - lag(created_at) OVER (ORDER BY created_at)))) as avg_interval_seconds
FROM github_api_calls 
WHERE created_at > now() - interval '24 hours'
GROUP BY endpoint;
```

### **Failed Webhook Analysis**
```sql
-- Recent failed webhooks
SELECT * FROM github_api_calls 
WHERE response_status >= 400 
   OR response_status IS NULL
ORDER BY created_at DESC;
```

---

## 🔄 **Advanced Use Cases**

### **1. Automated Code Review Notifications**
When PRs are opened, automatically:
- Create database records for tracking
- Notify team members via additional webhooks
- Update project management tools

### **2. Issue-Driven Development**
- GitHub issues create database tasks
- Database changes update GitHub issue status
- Bidirectional sync for project tracking

### **3. Deployment Automation**
- Push events trigger deployment pipelines
- Database changes create deployment records
- Status updates sent back to GitHub

### **4. Candidate Application Workflow**
- New candidates create GitHub issues for HR team
- GitHub issue comments update candidate status
- Automated interview scheduling

---

## 🛠️ **Troubleshooting**

### **Common Issues**

1. **"Webhook not receiving events"**
   - Check webhook URL is correct
   - Verify Edge Function is deployed
   - Check GitHub webhook settings

2. **"Signature verification failed"**
   - Ensure webhook secret matches
   - Check secret is set in Supabase
   - Verify signature algorithm

3. **"Database triggers not firing"**
   - Check trigger function exists
   - Verify pg_net extension is enabled
   - Look for function error messages

4. **"GitHub API calls failing"**
   - Verify GitHub token permissions
   - Check API rate limits
   - Update repository names in functions

### **Debug Commands**

```sql
-- Check if pg_net is working
SELECT net.http_get('https://httpbin.org/get');

-- Check recent pg_net responses
SELECT * FROM net._http_response 
ORDER BY created desc LIMIT 10;

-- Verify trigger functions exist
SELECT proname, prosrc FROM pg_proc 
WHERE proname LIKE '%github%';
```

---

## 📞 **Support**

If you need help:
1. Check the Edge Function logs first
2. Review database webhook logs
3. Test with simple payloads
4. Check GitHub webhook delivery logs

The webhook integration provides powerful automation between GitHub and your Supabase project. Start with simple use cases and expand as needed! 