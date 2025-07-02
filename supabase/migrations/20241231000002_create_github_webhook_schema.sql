-- GitHub Webhook Integration Schema
-- This migration creates tables to store GitHub webhook events and related data

-- Table to log all incoming GitHub webhook events
CREATE TABLE github_webhook_logs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  event_type text NOT NULL,
  action text,
  repository_name text,
  sender text,
  payload jsonb NOT NULL,
  processed_at timestamptz DEFAULT now(),
  created_at timestamptz DEFAULT now()
);

-- Table to store GitHub commits
CREATE TABLE github_commits (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  commit_sha text NOT NULL,
  repository_name text NOT NULL,
  message text,
  author_name text,
  author_email text,
  commit_url text,
  created_at timestamptz DEFAULT now(),
  UNIQUE(commit_sha, repository_name)
);

-- Table to store GitHub pull requests
CREATE TABLE github_pull_requests (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  pr_number integer NOT NULL,
  repository_name text NOT NULL,
  title text,
  state text,
  author text,
  pr_url text,
  action text,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now(),
  UNIQUE(pr_number, repository_name)
);

-- Table to store GitHub issues
CREATE TABLE github_issues (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  issue_number integer NOT NULL,
  repository_name text NOT NULL,
  title text,
  state text,
  author text,
  issue_url text,
  action text,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now(),
  UNIQUE(issue_number, repository_name)
);

-- Table to store GitHub repositories
CREATE TABLE github_repositories (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  repository_name text NOT NULL UNIQUE,
  repository_url text,
  action text,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Table to store GitHub API calls (for outbound webhooks)
CREATE TABLE github_api_calls (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  endpoint text NOT NULL,
  method text NOT NULL DEFAULT 'POST',
  payload jsonb,
  response_status integer,
  response_body text,
  triggered_by_table text,
  triggered_by_id uuid,
  created_at timestamptz DEFAULT now()
);

-- Indexes for better performance
CREATE INDEX idx_github_webhook_logs_event_type ON github_webhook_logs(event_type);
CREATE INDEX idx_github_webhook_logs_repository ON github_webhook_logs(repository_name);
CREATE INDEX idx_github_webhook_logs_processed_at ON github_webhook_logs(processed_at);

CREATE INDEX idx_github_commits_repository ON github_commits(repository_name);
CREATE INDEX idx_github_commits_created_at ON github_commits(created_at);

CREATE INDEX idx_github_prs_repository ON github_pull_requests(repository_name);
CREATE INDEX idx_github_prs_state ON github_pull_requests(state);

CREATE INDEX idx_github_issues_repository ON github_issues(repository_name);
CREATE INDEX idx_github_issues_state ON github_issues(state);

CREATE INDEX idx_github_api_calls_endpoint ON github_api_calls(endpoint);
CREATE INDEX idx_github_api_calls_created_at ON github_api_calls(created_at);

-- Enable Row Level Security
ALTER TABLE github_webhook_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE github_commits ENABLE ROW LEVEL SECURITY;
ALTER TABLE github_pull_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE github_issues ENABLE ROW LEVEL SECURITY;
ALTER TABLE github_repositories ENABLE ROW LEVEL SECURITY;
ALTER TABLE github_api_calls ENABLE ROW LEVEL SECURITY;

-- RLS Policies (adjust based on your security requirements)
-- For now, allow authenticated users to read all webhook data
CREATE POLICY "Allow authenticated read access" ON github_webhook_logs
  FOR SELECT TO authenticated USING (true);

CREATE POLICY "Allow authenticated read access" ON github_commits
  FOR SELECT TO authenticated USING (true);

CREATE POLICY "Allow authenticated read access" ON github_pull_requests
  FOR SELECT TO authenticated USING (true);

CREATE POLICY "Allow authenticated read access" ON github_issues
  FOR SELECT TO authenticated USING (true);

CREATE POLICY "Allow authenticated read access" ON github_repositories
  FOR SELECT TO authenticated USING (true);

CREATE POLICY "Allow authenticated read access" ON github_api_calls
  FOR SELECT TO authenticated USING (true);

-- Allow service role to do everything (for the Edge Function)
CREATE POLICY "Allow service role full access" ON github_webhook_logs
  FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Allow service role full access" ON github_commits
  FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Allow service role full access" ON github_pull_requests
  FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Allow service role full access" ON github_issues
  FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Allow service role full access" ON github_repositories
  FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Allow service role full access" ON github_api_calls
  FOR ALL TO service_role USING (true) WITH CHECK (true); 