import json
import hmac
import hashlib
import os
from datetime import datetime
from fastapi import Request, HTTPException
from typing import Dict, Any

def verify_github_signature(body: bytes, signature: str, secret: str) -> bool:
    """Verify GitHub webhook signature"""
    if not signature or not secret:
        return True  # Skip verification if not configured
    
    if not signature.startswith('sha256='):
        return False
    
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        body,
        hashlib.sha256
    ).hexdigest()
    
    provided_signature = signature[7:]  # Remove 'sha256=' prefix
    return hmac.compare_digest(expected_signature, provided_signature)

def verify_vercel_signature(body: bytes, signature: str, secret: str) -> bool:
    """Verify Vercel webhook signature"""
    if not signature or not secret:
        return True  # Skip verification if not configured
    
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        body,
        hashlib.sha1
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)

async def handle_github_webhook(request: Request) -> Dict[str, Any]:
    """Handle incoming GitHub webhook"""
    try:
        body = await request.body()
        signature = request.headers.get('x-hub-signature-256', '')
        event_type = request.headers.get('x-github-event', '')
        delivery_id = request.headers.get('x-github-delivery', '')
        
        github_secret = os.getenv('GITHUB_WEBHOOK_SECRET', '')
        
        # Verify signature if secret is configured
        if github_secret and not verify_github_signature(body, signature, github_secret):
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        payload = json.loads(body.decode('utf-8'))
        
        print(f"Received GitHub webhook: {event_type} (delivery: {delivery_id})")
        
        # Handle different GitHub events
        result = {"success": True, "event_type": event_type, "delivery_id": delivery_id}
        
        if event_type == 'push':
            result["commits"] = len(payload.get('commits', []))
            result["ref"] = payload.get('ref', '')
            result["repository"] = payload.get('repository', {}).get('full_name', '')
            
        elif event_type == 'pull_request':
            pr = payload.get('pull_request', {})
            result["action"] = payload.get('action', '')
            result["pr_number"] = pr.get('number', '')
            result["pr_title"] = pr.get('title', '')
            
        elif event_type == 'issues':
            issue = payload.get('issue', {})
            result["action"] = payload.get('action', '')
            result["issue_number"] = issue.get('number', '')
            result["issue_title"] = issue.get('title', '')
        
        return result
        
    except Exception as e:
        print(f"Error processing GitHub webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def handle_vercel_webhook(request: Request) -> Dict[str, Any]:
    """Handle incoming Vercel webhook"""
    try:
        body = await request.body()
        signature = request.headers.get('x-vercel-signature', '')
        
        vercel_secret = os.getenv('VERCEL_WEBHOOK_SECRET', '')
        
        # Verify signature if secret is configured
        if vercel_secret and not verify_vercel_signature(body, signature, vercel_secret):
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        payload = json.loads(body.decode('utf-8'))
        event_type = payload.get('type', '')
        
        print(f"Received Vercel webhook: {event_type}")
        
        result = {"success": True, "event_type": event_type}
        
        if 'deployment' in event_type:
            deployment = payload.get('data', {}).get('deployment', {})
            project = payload.get('data', {}).get('project', {})
            
            result.update({
                "deployment_id": deployment.get('id', ''),
                "deployment_url": deployment.get('url', ''),
                "deployment_state": deployment.get('state', ''),
                "project_name": project.get('name', ''),
                "type": deployment.get('type', ''),
                "creator": deployment.get('creator', {}).get('username', '')
            })
            
            # Add GitHub info if available
            meta = deployment.get('meta', {})
            if meta.get('githubCommitSha'):
                result["github_commit"] = {
                    "sha": meta.get('githubCommitSha', ''),
                    "message": meta.get('githubCommitMessage', ''),
                    "author": meta.get('githubCommitAuthorName', ''),
                    "ref": meta.get('githubCommitRef', ''),
                    "repo": meta.get('githubRepo', '')
                }
        
        return result
        
    except Exception as e:
        print(f"Error processing Vercel webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))
