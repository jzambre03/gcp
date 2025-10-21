#!/usr/bin/env python3
"""
Webhook Server for Demo - Blocks MRs from feature_branch_1 in cxp-ptg-adapter repo

Usage:
    python webhook_validator.py --token YOUR_GITLAB_TOKEN --port 5000
"""

import argparse
import json
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# HARDCODED FOR YOUR DEMO
GITLAB_URL = "https://gitlab.verizon.com"
TARGET_REPO = "saja9l7/cxp-ptg-adapter"  # Your specific repo
BLOCKED_BRANCH = "feature_branch_1"       # Branch to block
GITLAB_TOKEN = None


def post_gitlab_status(project_id, commit_sha, state, description):
    """
    Post commit status to GitLab
    
    Args:
        project_id: GitLab project ID
        commit_sha: Commit SHA
        state: 'pending', 'running', 'success', 'failed', 'canceled'
        description: Status description
    """
    url = f"{GITLAB_URL}/api/v4/projects/{project_id}/statuses/{commit_sha}"
    
    headers = {
        'PRIVATE-TOKEN': GITLAB_TOKEN,
        'Content-Type': 'application/json'
    }
    
    payload = {
        "state": state,
        "name": "config-validation",
        "description": description,
        "context": "config-validation"
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        print(f"✓ Posted '{state}' status to GitLab for commit {commit_sha[:8]}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"✗ Failed to post status to GitLab: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"  Response: {e.response.text}")
        return False


@app.route('/webhook', methods=['POST'])
def webhook_handler():
    """
    Handle GitLab webhook events - Block MRs from specific branch
    """
    try:
        data = request.json
        event_type = request.headers.get('X-Gitlab-Event', 'Unknown')
        
        print(f"\n{'='*60}")
        print(f"📥 Received webhook: {event_type}")
        print(f"{'='*60}")
        
        # Only process Merge Request events
        if event_type != 'Merge Request Hook':
            print(f"ℹ️  Ignoring non-MR event: {event_type}")
            return jsonify({"status": "ignored"}), 200
        
        # Extract MR info
        mr_data = data.get('object_attributes', {})
        mr_action = mr_data.get('action')
        mr_iid = mr_data.get('iid')
        mr_title = mr_data.get('title')
        source_branch = mr_data.get('source_branch')
        target_branch = mr_data.get('target_branch')
        commit_sha = mr_data.get('last_commit', {}).get('id')
        
        project = data.get('project', {})
        project_id = project.get('id')
        project_name = project.get('name')
        project_path = project.get('path_with_namespace')
        
        print(f"📋 MR Info:")
        print(f"   MR !{mr_iid}: {mr_title}")
        print(f"   Project: {project_path}")
        print(f"   Branch: {source_branch} → {target_branch}")
        print(f"   Commit: {commit_sha[:8] if commit_sha else 'N/A'}")
        
        # VALIDATE THIS IS THE CORRECT REPO
        if project_path != TARGET_REPO:
            print(f"⚠️  Ignoring webhook - not from target repo")
            print(f"   Expected: {TARGET_REPO}")
            print(f"   Got: {project_path}")
            return jsonify({"status": "ignored", "reason": "wrong repository"}), 200
        
        # Only process on 'open' or 'update'
        if mr_action not in ['open', 'update', 'reopen']:
            print(f"ℹ️  Skipping - action is '{mr_action}'")
            return jsonify({"status": "skipped"}), 200
        
        if not commit_sha:
            print("⚠️  No commit SHA found")
            return jsonify({"status": "error"}), 400
        
        # CHECK IF THIS IS THE BLOCKED BRANCH
        print(f"\n🔍 Checking branch: {source_branch}")
        
        if source_branch == BLOCKED_BRANCH:
            # BLOCK THIS MR - Post FAILED status
            print(f"❌ BLOCKING MR - Branch '{source_branch}' is blocked for demo")
            
            description = f"✗ Configuration validation failed: Changes from '{source_branch}' violate security policies"
            post_gitlab_status(project_id, commit_sha, "failed", description)
            
            print(f"{'='*60}\n")
            return jsonify({
                "status": "blocked",
                "branch": source_branch,
                "reason": "Demo branch - automatically blocked"
            }), 200
        else:
            # Allow other branches - Post SUCCESS status
            print(f"✅ ALLOWING MR - Branch '{source_branch}' is allowed")
            
            description = "✓ Configuration validation passed"
            post_gitlab_status(project_id, commit_sha, "success", description)
            
            print(f"{'='*60}\n")
            return jsonify({
                "status": "allowed",
                "branch": source_branch
            }), 200
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "config-validator"}), 200


@app.route('/', methods=['GET'])
def index():
    """Root endpoint"""
    return jsonify({
        "service": "GitLab Config Validator",
        "status": "running",
        "webhook_endpoint": "/webhook",
        "health_endpoint": "/health"
    }), 200


def main():
    parser = argparse.ArgumentParser(
        description='Webhook server for cxp-ptg-adapter demo - blocks feature_branch_1',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  python webhook_validator.py --token glpat-xxxxx
        """
    )
    
    parser.add_argument('--token',
                       required=True,
                       help='GitLab personal access token (api scope)')
    
    parser.add_argument('--port',
                       type=int,
                       default=5000,
                       help='Port to run server on (default: 5000)')
    
    args = parser.parse_args()
    
    global GITLAB_TOKEN
    GITLAB_TOKEN = args.token
    
    print("="*60)
    print("🚀 GitLab MR Blocker - Demo Webhook Server")
    print("="*60)
    print(f"GitLab URL: {GITLAB_URL}")
    print(f"Target Repo: {TARGET_REPO}")
    print(f"Blocked Branch: {BLOCKED_BRANCH}")
    print(f"Local Port: {args.port}")
    print(f"Webhook URL: http://localhost:{args.port}/webhook")
    print("="*60)
    print(f"\n📌 MRs from '{BLOCKED_BRANCH}' in '{TARGET_REPO}' will be BLOCKED")
    print(f"✅ All other branches will PASS")
    print(f"⚠️  Webhooks from other repos will be IGNORED\n")
    print("⚠️  Expose this server using ngrok or cloudflare tunnel:")
    print(f"   ngrok http {args.port}")
    print(f"   cloudflared tunnel --url http://localhost:{args.port}\n")
    
    # Run Flask server
    app.run(host='0.0.0.0', port=args.port, debug=False)


if __name__ == '__main__':
    main()

