# GitHub ↔ Supabase Integration Guide

## 🎯 Overview
This guide will help you connect your GitHub repository with Supabase for automated deployments and CI/CD.

## 📋 Prerequisites
- [x] GitHub repository: `jobportal_connector` 
- [x] Supabase project: `cwovxotrzvwutwtlgozb` (jobportal_connector)
- [x] GitHub Actions workflow already created

## 🔑 Step 1: Get Supabase Credentials

### 1.1 Project API Keys
Go to: https://supabase.com/dashboard/project/cwovxotrzvwutwtlgozb/settings/api

Copy these values:
- **Project URL**: `https://cwovxotrzvwutwtlgozb.supabase.co`
- **anon public**: `eyJ...` (for frontend)
- **service_role**: `eyJ...` (for backend - keep secret!)

### 1.2 Access Token for CLI
Go to: https://supabase.com/dashboard/account/tokens
- Create a new **Access Token**
- Copy the token value

### 1.3 Database Password
Go to: https://supabase.com/dashboard/project/cwovxotrzvwutwtlgozb/settings/database
- Note down your **Database Password** (or reset if forgotten)

## 🔧 Step 2: Configure GitHub Repository

### 2.1 Set GitHub Secrets
Go to: `https://github.com/YOUR_USERNAME/jobportal_connector/settings/secrets/actions`

Add these repository secrets:

| Secret Name | Value | Description |
|-------------|--------|-------------|
| `SUPABASE_URL` | `https://cwovxotrzvwutwtlgozb.supabase.co` | Your project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | `eyJ...` | Service role key from Step 1.1 |
| `SUPABASE_ACCESS_TOKEN` | `sbp_...` | Access token from Step 1.2 |
| `SUPABASE_DB_PASSWORD` | `your_db_password` | Database password from Step 1.3 |
| `SUPABASE_PROJECT_ID` | `cwovxotrzvwutwtlgozb` | Your project reference ID |
| `BROWSER_USE_API_KEY` | `your_api_key` | Browser-Use API key |
| `VERCEL_TOKEN` | `your_vercel_token` | Vercel deployment token |

### 2.2 Update Local Environment
Update your local `.env` file:

```bash
SUPABASE_URL=https://cwovxotrzvwutwtlgozb.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here
BROWSER_USE_API_KEY=your_browser_use_api_key_here
```

## 🗄️ Step 3: Deploy Database Schema

### Option A: Manual (Recommended first time)
1. Go to: https://supabase.com/dashboard/project/cwovxotrzvwutwtlgozb/sql/new
2. Copy and paste the SQL from `supabase/migrations/20241231000001_create_job_scraper_schema.sql`
3. Click "Run" to create tables

### Option B: CLI (after linking project)
```bash
# Link project (requires database password)
supabase link --project-ref cwovxotrzvwutwtlgozb

# Push migrations
supabase db push
```

## 🚀 Step 4: Test the Integration

### 4.1 Test Supabase Connection
```bash
# Install dependencies
pip install -r requirements.txt

# Test connection
python test_supabase_connection.py
```

### 4.2 Test GitHub Actions
1. Make a small change to README.md
2. Commit and push to main branch:
```bash
git add .
git commit -m "test: trigger GitHub Actions"
git push origin main
```
3. Check Actions tab: `https://github.com/YOUR_USERNAME/jobportal_connector/actions`

## 🔄 Step 5: Automatic Deployment Flow

Once connected, this workflow happens automatically:

1. **Code Push** → GitHub detects changes
2. **GitHub Actions** → Runs tests and linting
3. **Supabase Migration** → Applies database changes
4. **Vercel Deploy** → Deploys API to production
5. **Notification** → Get deployment status

## ✅ Verification Checklist

- [ ] GitHub secrets configured
- [ ] Supabase tables created (companies, positions, candidates)
- [ ] Local `.env` file updated
- [ ] `test_supabase_connection.py` passes
- [ ] GitHub Actions workflow completes successfully
- [ ] API endpoints accessible via Vercel

## 🛠️ Troubleshooting

### Common Issues:

**Connection Failed**
- Verify SUPABASE_URL and SERVICE_ROLE_KEY
- Check project reference ID is correct

**Migration Failed**
- Ensure database password is correct
- Try manual SQL execution first

**GitHub Actions Failed**
- Check all secrets are set correctly
- Verify SUPABASE_ACCESS_TOKEN has proper permissions

## 🔗 Useful Links

- **Supabase Dashboard**: https://supabase.com/dashboard/project/cwovxotrzvwutwtlgozb
- **GitHub Repository**: https://github.com/YOUR_USERNAME/jobportal_connector
- **GitHub Actions**: https://github.com/YOUR_USERNAME/jobportal_connector/actions
- **Vercel Dashboard**: https://vercel.com/dashboard

---

## 🎉 Next Steps After Setup

Once integration is working:
1. Set up Browser-Use API key
2. Test the `/api/scrape` endpoint
3. Configure job portal credentials
4. Run end-to-end scraping test 

## 🔧 **Option A: Manual SQL (Recommended - 2 minutes)**

1. **Go to Supabase SQL Editor:**
   ```
   https://supabase.com/dashboard/project/cwovxotrzvwutwtlgozb/sql/new
   ```

2. **Copy and paste this SQL:**
   ```sql
   -- Create companies table
   create table companies (
     id uuid primary key default gen_random_uuid(),
     name text not null unique,
     created_at timestamptz default now()
   );

   -- Create positions table
   create table positions (
     id uuid primary key default gen_random_uuid(),
     company_id uuid references companies(id) on delete cascade,
     title text not null,
     external_job_id text,         -- id z portálu, pro snadné párování
     created_at timestamptz default now()
   );

   -- Create candidates table
   create table candidates (
     id uuid primary key default gen_random_uuid(),
     position_id uuid references positions(id) on delete cascade,
     first_name text, 
     last_name text,
     email text, 
     phone text,
     phone_sha256 text generated always as (encode(digest(phone, 'sha256'), 'hex')) stored,
     source_url text,
     created_at timestamptz default now(),
     unique(position_id, phone_sha256)          -- technická bariéra proti duplicitám
   );

   -- Add indexes for better performance
   create index idx_candidates_position_id on candidates(position_id);
   create index idx_positions_company_id on positions(company_id);
   create index idx_candidates_phone_sha256 on candidates(phone_sha256);
   ```

3. **Click "Run"** to execute the SQL

## 🔧 **Option B: CLI Setup (Advanced)**

If you want to use the CLI properly for future migrations:

### Step 1: Link the project
You'll need your database password from Supabase Dashboard → Settings → Database

### Step 2: Initialize migration history
After linking, you can sync the migrations:

```bash
# This would apply the migration files to Supabase
supabase db push
```

## ✅ **Verification**

After running the SQL manually, you can verify it worked:

1. **Check Tables:** Go to https://supabase.com/dashboard/project/cwovxotrzvwutwtlgozb/editor
2. **You should see:** 3 tables (companies, positions, candidates)
3. **Test Connection:** Update your `.env` file and run `python test_supabase_connection.py`

## 🎯 **Recommended Approach**

For now, **use Option A (Manual SQL)** because:
- ✅ It's fastest (2 minutes)
- ✅ No CLI setup needed
- ✅ Gets you working immediately
- ✅ GitHub Actions will handle future migrations

After you run the SQL manually and confirm everything works, we can set up the CLI properly for future migrations.

**Try the manual SQL approach first - let me know if you run into any issues!** 

## ✅ **Verify Tables Were Created**

1. **Go to Table Editor:**
   ```
   https://supabase.com/dashboard/project/cwovxotrzvwutwtlgozb/editor
   ```

2. **You should see 3 new tables:**
   - `companies`
   - `positions` 
   - `candidates`

## 🔧 **Next Steps:**

### **Step 1: Update Your Local Environment**
Update your `.env` file with the real credentials:

```bash
SUPABASE_URL=https://cwovxotrzvwutwtlgozb.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_actual_service_role_key_here
BROWSER_USE_API_KEY=your_browser_use_api_key_here
```

Get the `SUPABASE_SERVICE_ROLE_KEY` from:
https://supabase.com/dashboard/project/cwovxotrzvwutwtlgozb/settings/api

### **Step 2: Test the Connection**
Run the connection test:

```bash
pip install -r requirements.txt
python test_supabase_connection.py
```

### **Step 3: Set GitHub Secrets**
Add these secrets to your GitHub repository:
https://github.com/mfortelny/jobportal_connector/settings/secrets/actions

| Secret Name | Value |
|-------------|-------|
| `SUPABASE_URL` | `https://cwovxotrzvwutwtlgozb.supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY` | Your service role key |
| `SUPABASE_PROJECT_ID` | `cwovxotrzvwutwtlgozb` |

## 🎯 **What You've Accomplished:**
- ✅ Database schema created
- ✅ Tables with proper relationships and constraints
- ✅ Duplicate prevention via phone number hashing
- ✅ Ready for the job scraping application

**Next, let's test the connection - update your `.env` file first, then run the test script!** 