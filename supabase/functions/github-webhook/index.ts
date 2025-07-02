import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { crypto } from 'https://deno.land/std@0.168.0/crypto/mod.ts'

interface GitHubWebhookEvent {
  action?: string
  repository?: {
    name: string
    full_name: string
    html_url: string
  }
  sender?: {
    login: string
    avatar_url: string
  }
  commits?: Array<{
    id: string
    message: string
    author: {
      name: string
      email: string
    }
    url: string
  }>
  pull_request?: {
    number: number
    title: string
    html_url: string
    state: string
    user: {
      login: string
    }
  }
  issue?: {
    number: number
    title: string
    html_url: string
    state: string
    user: {
      login: string
    }
  }
}

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type, x-github-event, x-hub-signature-256',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
}

async function verifyGitHubSignature(body: string, signature: string, secret: string): Promise<boolean> {
  const encoder = new TextEncoder()
  const key = await crypto.subtle.importKey(
    'raw',
    encoder.encode(secret),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign']
  )
  
  const expectedSignature = await crypto.subtle.sign('HMAC', key, encoder.encode(body))
  const expectedHex = 'sha256=' + Array.from(new Uint8Array(expectedSignature))
    .map(b => b.toString(16).padStart(2, '0'))
    .join('')
  
  return signature === expectedHex
}

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  if (req.method !== 'POST') {
    return new Response('Method not allowed', { status: 405, headers: corsHeaders })
  }

  try {
    // Get environment variables
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!
    const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    const githubWebhookSecret = Deno.env.get('GITHUB_WEBHOOK_SECRET')

    // Initialize Supabase client
    const supabase = createClient(supabaseUrl, supabaseServiceKey)

    // Get request body and headers
    const body = await req.text()
    const signature = req.headers.get('x-hub-signature-256')
    const githubEvent = req.headers.get('x-github-event')

    // Verify GitHub webhook signature (if secret is configured)
    if (githubWebhookSecret && signature) {
      const isValid = await verifyGitHubSignature(body, signature, githubWebhookSecret)
      if (!isValid) {
        console.error('Invalid GitHub webhook signature')
        return new Response('Unauthorized', { status: 401, headers: corsHeaders })
      }
    }

    // Parse the webhook payload
    const payload: GitHubWebhookEvent = JSON.parse(body)

    console.log(`Received GitHub webhook: ${githubEvent}`, {
      action: payload.action,
      repository: payload.repository?.full_name,
      sender: payload.sender?.login
    })

    // Store webhook event in database
    const { error: logError } = await supabase
      .from('github_webhook_logs')
      .insert({
        event_type: githubEvent,
        action: payload.action,
        repository_name: payload.repository?.full_name,
        sender: payload.sender?.login,
        payload: payload,
        processed_at: new Date().toISOString()
      })

    if (logError) {
      console.error('Error logging webhook:', logError)
    }

    // Handle different GitHub events
    switch (githubEvent) {
      case 'push':
        await handlePushEvent(supabase, payload)
        break
      
      case 'pull_request':
        await handlePullRequestEvent(supabase, payload)
        break
      
      case 'issues':
        await handleIssueEvent(supabase, payload)
        break
      
      case 'repository':
        await handleRepositoryEvent(supabase, payload)
        break
      
      default:
        console.log(`Unhandled GitHub event: ${githubEvent}`)
    }

    return new Response(
      JSON.stringify({ 
        message: 'Webhook processed successfully',
        event: githubEvent,
        action: payload.action 
      }),
      { 
        status: 200, 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      }
    )

  } catch (error) {
    console.error('Error processing webhook:', error)
    return new Response(
      JSON.stringify({ error: 'Internal server error' }),
      { 
        status: 500, 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      }
    )
  }
})

async function handlePushEvent(supabase: any, payload: GitHubWebhookEvent) {
  if (!payload.commits || !payload.repository) return

  // Store commit information
  for (const commit of payload.commits) {
    const { error } = await supabase
      .from('github_commits')
      .insert({
        commit_sha: commit.id,
        repository_name: payload.repository.full_name,
        message: commit.message,
        author_name: commit.author.name,
        author_email: commit.author.email,
        commit_url: commit.url,
        created_at: new Date().toISOString()
      })

    if (error) {
      console.error('Error storing commit:', error)
    }
  }

  // Trigger any automated actions based on push events
  console.log(`Processed ${payload.commits.length} commits from ${payload.repository.full_name}`)
}

async function handlePullRequestEvent(supabase: any, payload: GitHubWebhookEvent) {
  if (!payload.pull_request || !payload.repository) return

  const { error } = await supabase
    .from('github_pull_requests')
    .upsert({
      pr_number: payload.pull_request.number,
      repository_name: payload.repository.full_name,
      title: payload.pull_request.title,
      state: payload.pull_request.state,
      author: payload.pull_request.user.login,
      pr_url: payload.pull_request.html_url,
      action: payload.action,
      updated_at: new Date().toISOString()
    }, {
      onConflict: 'pr_number,repository_name'
    })

  if (error) {
    console.error('Error storing pull request:', error)
  }

  console.log(`Processed PR #${payload.pull_request.number} - ${payload.action}`)
}

async function handleIssueEvent(supabase: any, payload: GitHubWebhookEvent) {
  if (!payload.issue || !payload.repository) return

  const { error } = await supabase
    .from('github_issues')
    .upsert({
      issue_number: payload.issue.number,
      repository_name: payload.repository.full_name,
      title: payload.issue.title,
      state: payload.issue.state,
      author: payload.issue.user.login,
      issue_url: payload.issue.html_url,
      action: payload.action,
      updated_at: new Date().toISOString()
    }, {
      onConflict: 'issue_number,repository_name'
    })

  if (error) {
    console.error('Error storing issue:', error)
  }

  console.log(`Processed Issue #${payload.issue.number} - ${payload.action}`)
}

async function handleRepositoryEvent(supabase: any, payload: GitHubWebhookEvent) {
  if (!payload.repository) return

  const { error } = await supabase
    .from('github_repositories')
    .upsert({
      repository_name: payload.repository.full_name,
      repository_url: payload.repository.html_url,
      action: payload.action,
      updated_at: new Date().toISOString()
    }, {
      onConflict: 'repository_name'
    })

  if (error) {
    console.error('Error storing repository info:', error)
  }

  console.log(`Processed repository event: ${payload.repository.full_name} - ${payload.action}`)
} 