-- Database Webhook Triggers for GitHub Integration
-- This migration creates triggers that automatically call GitHub API when database records change

-- Function to call GitHub API when candidates are added
CREATE OR REPLACE FUNCTION notify_github_new_candidate()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  company_name_var text;
  position_title_var text;
  github_token text;
  webhook_url text;
  payload jsonb;
  request_id bigint;
BEGIN
  -- Get company and position details
  SELECT c.name, p.title 
  INTO company_name_var, position_title_var
  FROM companies c
  JOIN positions p ON p.company_id = c.id
  WHERE p.id = NEW.position_id;

  -- Get GitHub token from secrets (you'll need to set this)
  -- For demo purposes, we'll use a placeholder
  github_token := 'github_pat_your_token_here';
  
  -- GitHub API endpoint for creating issues or discussions
  webhook_url := 'https://api.github.com/repos/your-username/your-repo/issues';

  -- Build the payload for GitHub issue creation
  payload := jsonb_build_object(
    'title', 'New Candidate Applied: ' || coalesce(NEW.first_name, '') || ' ' || coalesce(NEW.last_name, ''),
    'body', format(
      'A new candidate has applied for the position **%s** at **%s**.\n\n' ||
      '**Candidate Details:**\n' ||
      '- Name: %s %s\n' ||
      '- Email: %s\n' ||
      '- Phone: %s\n' ||
      '- Applied: %s\n\n' ||
      '[View in Dashboard](%s)',
      position_title_var,
      company_name_var,
      coalesce(NEW.first_name, 'N/A'),
      coalesce(NEW.last_name, 'N/A'),
      coalesce(NEW.email, 'N/A'),
      coalesce(NEW.phone, 'N/A'),
      NEW.created_at,
      NEW.source_url
    ),
    'labels', jsonb_build_array('candidate', 'new-application')
  );

  -- Make HTTP request to GitHub API using pg_net
  SELECT net.http_post(
    url := webhook_url,
    headers := jsonb_build_object(
      'Authorization', 'Bearer ' || github_token,
      'Accept', 'application/vnd.github+json',
      'Content-Type', 'application/json',
      'X-GitHub-Api-Version', '2022-11-28'
    ),
    body := payload,
    timeout_milliseconds := 10000
  ) INTO request_id;

  -- Log the API call
  INSERT INTO github_api_calls (
    endpoint,
    method,
    payload,
    triggered_by_table,
    triggered_by_id
  ) VALUES (
    webhook_url,
    'POST',
    payload,
    'candidates',
    NEW.id
  );

  RETURN NEW;
EXCEPTION
  WHEN OTHERS THEN
    -- Log error but don't fail the original operation
    RAISE WARNING 'GitHub API call failed: %', SQLERRM;
    RETURN NEW;
END;
$$;

-- Function to notify GitHub when job scraping completes
CREATE OR REPLACE FUNCTION notify_github_scraping_completed()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  candidate_count integer;
  github_token text;
  webhook_url text;
  payload jsonb;
  request_id bigint;
BEGIN
  -- Only trigger on INSERT (new scraping jobs)
  IF TG_OP != 'INSERT' THEN
    RETURN NEW;
  END IF;

  -- Count candidates for this position
  SELECT COUNT(*) INTO candidate_count
  FROM candidates
  WHERE position_id = NEW.position_id;

  github_token := 'github_pat_your_token_here';
  webhook_url := 'https://api.github.com/repos/your-username/your-repo/issues';

  -- Create GitHub issue about scraping completion
  payload := jsonb_build_object(
    'title', 'Job Scraping Completed',
    'body', format(
      'Job scraping has been completed for position ID: %s\n\n' ||
      '**Results:**\n' ||
      '- Total candidates found: %s\n' ||
      '- Position: %s\n' ||
      '- Scraped at: %s\n\n' ||
      'Check the candidates table for details.',
      NEW.position_id,
      candidate_count,
      'Position ID ' || NEW.position_id,
      now()
    ),
    'labels', jsonb_build_array('automation', 'scraping-complete')
  );

  -- Make the API call
  SELECT net.http_post(
    url := webhook_url,
    headers := jsonb_build_object(
      'Authorization', 'Bearer ' || github_token,
      'Accept', 'application/vnd.github+json',
      'Content-Type', 'application/json',
      'X-GitHub-Api-Version', '2022-11-28'
    ),
    body := payload,
    timeout_milliseconds := 10000
  ) INTO request_id;

  -- Log the API call
  INSERT INTO github_api_calls (
    endpoint,
    method,
    payload,
    triggered_by_table,
    triggered_by_id
  ) VALUES (
    webhook_url,
    'POST',
    payload,
    'candidates',
    NEW.id
  );

  RETURN NEW;
EXCEPTION
  WHEN OTHERS THEN
    RAISE WARNING 'GitHub API call failed: %', SQLERRM;
    RETURN NEW;
END;
$$;

-- Function to create GitHub repository webhooks for monitoring
CREATE OR REPLACE FUNCTION setup_github_repository_webhook()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  github_token text;
  webhook_url text;
  repo_webhook_url text;
  payload jsonb;
  request_id bigint;
BEGIN
  -- Only trigger on INSERT (new repositories)
  IF TG_OP != 'INSERT' THEN
    RETURN NEW;
  END IF;

  github_token := 'github_pat_your_token_here';
  
  -- GitHub API endpoint for creating webhooks
  webhook_url := format('https://api.github.com/repos/%s/hooks', NEW.repository_name);
  
  -- Your Supabase Edge Function endpoint
  repo_webhook_url := 'https://your-project-ref.supabase.co/functions/v1/github-webhook';

  -- Payload for creating webhook
  payload := jsonb_build_object(
    'name', 'web',
    'active', true,
    'events', jsonb_build_array('push', 'pull_request', 'issues'),
    'config', jsonb_build_object(
      'url', repo_webhook_url,
      'content_type', 'json',
      'insecure_ssl', '0'
    )
  );

  -- Make API call to create webhook
  SELECT net.http_post(
    url := webhook_url,
    headers := jsonb_build_object(
      'Authorization', 'Bearer ' || github_token,
      'Accept', 'application/vnd.github+json',
      'Content-Type', 'application/json',
      'X-GitHub-Api-Version', '2022-11-28'
    ),
    body := payload,
    timeout_milliseconds := 10000
  ) INTO request_id;

  -- Log the API call
  INSERT INTO github_api_calls (
    endpoint,
    method,
    payload,
    triggered_by_table,
    triggered_by_id
  ) VALUES (
    webhook_url,
    'POST',
    payload,
    'github_repositories',
    NEW.id
  );

  RETURN NEW;
EXCEPTION
  WHEN OTHERS THEN
    RAISE WARNING 'GitHub webhook setup failed: %', SQLERRM;
    RETURN NEW;
END;
$$;

-- Function to send Database Webhook to external URL
CREATE OR REPLACE FUNCTION send_database_webhook()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  webhook_url text;
  payload jsonb;
  request_id bigint;
BEGIN
  -- External webhook URL (could be GitHub, Slack, Discord, etc.)
  webhook_url := 'https://your-external-webhook-url.com/webhook';

  -- Build payload with table change information
  payload := jsonb_build_object(
    'event_type', TG_OP,
    'table_name', TG_TABLE_NAME,
    'schema_name', TG_TABLE_SCHEMA,
    'timestamp', now(),
    'old_record', CASE WHEN TG_OP = 'DELETE' THEN to_jsonb(OLD) ELSE null END,
    'new_record', CASE WHEN TG_OP != 'DELETE' THEN to_jsonb(NEW) ELSE null END
  );

  -- Make HTTP request
  SELECT net.http_post(
    url := webhook_url,
    headers := jsonb_build_object(
      'Content-Type', 'application/json',
      'User-Agent', 'Supabase-Database-Webhook'
    ),
    body := payload,
    timeout_milliseconds := 5000
  ) INTO request_id;

  -- Log the webhook call
  INSERT INTO github_api_calls (
    endpoint,
    method,
    payload,
    triggered_by_table,
    triggered_by_id
  ) VALUES (
    webhook_url,
    'POST',
    payload,
    TG_TABLE_NAME,
    CASE WHEN TG_OP != 'DELETE' THEN NEW.id ELSE OLD.id END
  );

  -- Return appropriate record
  IF TG_OP = 'DELETE' THEN
    RETURN OLD;
  ELSE
    RETURN NEW;
  END IF;
EXCEPTION
  WHEN OTHERS THEN
    RAISE WARNING 'Database webhook failed: %', SQLERRM;
    IF TG_OP = 'DELETE' THEN
      RETURN OLD;
    ELSE
      RETURN NEW;
    END IF;
END;
$$;

-- Create triggers for different events

-- Trigger when new candidates are added
CREATE TRIGGER github_notify_new_candidate
  AFTER INSERT ON candidates
  FOR EACH ROW
  EXECUTE FUNCTION notify_github_new_candidate();

-- Trigger when new repositories are tracked
CREATE TRIGGER github_setup_repository_webhook
  AFTER INSERT ON github_repositories
  FOR EACH ROW
  EXECUTE FUNCTION setup_github_repository_webhook();

-- Generic database webhook for companies table
CREATE TRIGGER send_companies_webhook
  AFTER INSERT OR UPDATE OR DELETE ON companies
  FOR EACH ROW
  EXECUTE FUNCTION send_database_webhook();

-- Generic database webhook for positions table
CREATE TRIGGER send_positions_webhook
  AFTER INSERT OR UPDATE OR DELETE ON positions
  FOR EACH ROW
  EXECUTE FUNCTION send_database_webhook(); 