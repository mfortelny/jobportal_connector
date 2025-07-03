# 🚀 Vercel Deployment Guide - Default Settings

## Step-by-Step Deployment Process

### 1. Access Vercel Dashboard
- Go to: **https://vercel.com/new**
- Sign in with your GitHub account if not already logged in

### 2. Import Your Repository
1. You'll see "Import Git Repository" section
2. If your GitHub account isn't connected:
   - Click "Continue with GitHub"
   - Authorize Vercel to access your repositories
3. Find your repository: `mfortelny/jobportal_connector`
   - Use the search box if needed
   - Click "Import" next to your repository

### 3. Configure Project (Default Settings)
When you see the configuration screen, here are the **default settings** to use:

**Project Settings:**
- **Project Name**: `jobportal-connector` (auto-filled)
- **Framework Preset**: `Other` (auto-detected)
- **Root Directory**: `./` (leave as default)

**Build and Output Settings:**
- **Build Command**: (leave empty - auto-detected)
- **Output Directory**: (leave empty - auto-detected) 
- **Install Command**: (leave empty - auto-detected as `pip install -r requirements.txt`)

**Advanced Settings (Optional):**
- **Node.js Version**: (leave as default)
- **Environment Variables**: Skip for now - add after deployment

### 4. Deploy with Default Settings
1. Click the blue **"Deploy"** button
2. Vercel will:
   - Clone your repository
   - Install dependencies (`pip install -r requirements.txt`)
   - Build your application
   - Deploy to a URL like: `https://jobportal-connector-abc123.vercel.app`

### 5. Wait for Deployment
- Watch the build logs in real-time
- Deployment typically takes 1-3 minutes
- You'll see a success screen with your deployment URL

### 6. Test Your Deployment
Once deployed, you'll get a URL. Test it immediately:
```bash
curl https://your-deployment-url.vercel.app/api/health
```

## What Vercel Auto-Detects

For your Python FastAPI project, Vercel automatically:
- ✅ Detects it's a Python project
- ✅ Uses `pip install -r requirements.txt` 
- ✅ Serves your FastAPI app through `api/index.py`
- ✅ Sets up the proper routing via `vercel.json`
- ✅ Configures serverless functions

## After Deployment - Environment Variables Setup

### Required Environment Variables
Since you're using Supabase's native GitHub integration, add these to Vercel:

Go to: **Project → Settings → Environment Variables**

**Essential Variables:**
1. `SUPABASE_URL` → Your Supabase project URL (e.g., `https://abc123.supabase.co`)
2. `SUPABASE_SERVICE_ROLE_KEY` → Your Supabase service role key

**Optional Webhook Secrets (for security):**
3. `GITHUB_WEBHOOK_SECRET` → Random string for GitHub webhook verification
4. `VERCEL_WEBHOOK_SECRET` → Random string for Vercel webhook verification

### How to Get Supabase Values:
1. Go to your Supabase dashboard
2. Project Settings → API
3. Copy "Project URL" → Use for `SUPABASE_URL`
4. Copy "service_role" key → Use for `SUPABASE_SERVICE_ROLE_KEY`

**Important:** After adding environment variables, **redeploy** your project to apply them.

### Automatic GitHub Integration
Vercel automatically:
- Sets up a GitHub webhook
- Enables automatic deployments on push to main branch
- Creates preview deployments for pull requests

### Your New URLs
- **Production**: `https://jobportal-connector-xyz.vercel.app`
- **API Health**: `https://jobportal-connector-xyz.vercel.app/api/health`
- **GitHub Webhook**: `https://jobportal-connector-xyz.vercel.app/webhooks/github`
- **Vercel Webhook**: `https://jobportal-connector-xyz.vercel.app/webhooks/vercel`

## Troubleshooting

### If Build Fails
1. Check the build logs for errors
2. Common issues:
   - Missing dependencies in `requirements.txt`
   - Python version compatibility
   - File path issues

### If App Doesn't Start
1. Verify `api/index.py` exists
2. Check `vercel.json` configuration
3. Look for import errors in logs

### Environment Variable Errors
If you see "SUPABASE_URL references Secret" error:
1. ✅ **Fixed**: Updated `vercel.json` to remove secret references
2. Add environment variables manually in Vercel dashboard
3. Redeploy after adding variables

## Quick Environment Setup Commands

After deployment, set these in Vercel dashboard:
```
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here
GITHUB_WEBHOOK_SECRET=your-random-github-secret
VERCEL_WEBHOOK_SECRET=your-random-vercel-secret
```
