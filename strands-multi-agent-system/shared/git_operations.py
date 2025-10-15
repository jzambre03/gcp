"""
Git Operations Module - Handles Git branch creation and validation

This module provides functions to create branches, check if branches exist,
and manage Git operations for the drift detection system.
"""

import os
import tempfile
import shutil
import uuid
from pathlib import Path
from datetime import datetime
from typing import List, Optional
import logging

import git
from git.exc import GitCommandError

logger = logging.getLogger(__name__)


def generate_unique_branch_name(prefix: str, environment: str) -> str:
    """
    Generate a unique branch name with timestamp and UUID.
    
    Args:
        prefix: Branch prefix ("golden" or "drift")
        environment: Environment name (e.g., "prod", "dev", "qa", "staging")
        
    Returns:
        Unique branch name (e.g., "drift_prod_20251015_143052_abc123")
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:6]  # Short UUID for readability
    
    return f"{prefix}_{environment}_{timestamp}_{unique_id}"


def setup_git_auth(repo_url: str, gitlab_token: Optional[str] = None) -> str:
    """
    Set up Git authentication using environment variables or provided token.
    
    Args:
        repo_url: Repository URL
        gitlab_token: Optional GitLab personal access token
        
    Returns:
        Authenticated repository URL
    """
    token = gitlab_token or os.getenv('GITLAB_TOKEN')
    gitlab_username = os.getenv('GITLAB_USERNAME')
    gitlab_password = os.getenv('GITLAB_PASSWORD')
    
    if token:
        logger.info("Using GitLab personal access token for authentication")
        if repo_url.startswith('https://'):
            return repo_url.replace('https://', f'https://oauth2:{token}@')
    elif gitlab_username and gitlab_password:
        logger.info("Using username/password for authentication")
        if repo_url.startswith('https://'):
            return repo_url.replace('https://', f'https://{gitlab_username}:{gitlab_password}@')
    
    logger.warning("No authentication credentials found. Proceeding without auth")
    return repo_url


def check_branch_exists(repo_url: str, branch_name: str, gitlab_token: Optional[str] = None) -> bool:
    """
    Check if a branch exists on the remote repository.
    
    Args:
        repo_url: Repository URL
        branch_name: Branch name to check
        gitlab_token: Optional GitLab token for authentication
        
    Returns:
        True if branch exists, False otherwise
    """
    temp_dir = None
    try:
        # Create temporary directory for checking
        temp_dir = tempfile.mkdtemp(prefix="git_check_")
        
        # Setup authentication
        auth_url = setup_git_auth(repo_url, gitlab_token)
        
        # Clone with minimal depth (just to list refs)
        logger.info(f"Checking if branch {branch_name} exists in {repo_url}")
        repo = git.Repo.clone_from(auth_url, temp_dir, depth=1, single_branch=False, no_checkout=True)
        
        # Fetch remote refs
        repo.remotes.origin.fetch()
        
        # Check if branch exists in remote
        remote_branches = [ref.name for ref in repo.remotes.origin.refs]
        branch_exists = f"origin/{branch_name}" in remote_branches
        
        logger.info(f"Branch {branch_name} exists: {branch_exists}")
        return branch_exists
        
    except GitCommandError as e:
        logger.error(f"Git error checking branch {branch_name}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error checking branch {branch_name}: {e}")
        return False
    finally:
        # Cleanup temporary directory
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                logger.warning(f"Failed to cleanup temp directory {temp_dir}: {e}")


def create_branch_from_main(
    repo_url: str,
    main_branch: str,
    new_branch_name: str,
    gitlab_token: Optional[str] = None
) -> bool:
    """
    Create a new branch from the main branch and push it to remote.
    
    Args:
        repo_url: Repository URL
        main_branch: Source branch name (e.g., "main", "master")
        new_branch_name: Name for the new branch
        gitlab_token: Optional GitLab token for authentication
        
    Returns:
        True if successful, False otherwise
    """
    temp_dir = None
    try:
        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix="git_branch_create_")
        logger.info(f"Creating branch {new_branch_name} from {main_branch} in temp dir: {temp_dir}")
        
        # Setup authentication
        auth_url = setup_git_auth(repo_url, gitlab_token)
        
        # Clone the repository
        logger.info(f"Cloning repository from {main_branch}")
        repo = git.Repo.clone_from(auth_url, temp_dir, branch=main_branch)
        
        # Create new branch from main
        logger.info(f"Creating new branch: {new_branch_name}")
        new_branch = repo.create_head(new_branch_name)
        new_branch.checkout()
        
        # Push the new branch to remote
        logger.info(f"Pushing branch {new_branch_name} to remote")
        repo.git.push('--set-upstream', 'origin', new_branch_name)
        
        logger.info(f"✅ Successfully created and pushed branch {new_branch_name}")
        return True
        
    except GitCommandError as e:
        logger.error(f"Git error creating branch {new_branch_name}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error creating branch {new_branch_name}: {e}")
        return False
    finally:
        # Cleanup temporary directory
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                logger.info(f"Cleaned up temp directory: {temp_dir}")
            except Exception as e:
                logger.warning(f"Failed to cleanup temp directory {temp_dir}: {e}")


def create_config_only_branch(
    repo_url: str,
    main_branch: str,
    new_branch_name: str,
    config_paths: List[str],
    gitlab_token: Optional[str] = None
) -> bool:
    """
    Create a new branch containing ONLY configuration files (FAST - sparse checkout).
    This is much faster than cloning the entire repository.
    
    Args:
        repo_url: Repository URL
        main_branch: Source branch name (e.g., "main", "master")
        new_branch_name: Name for the new branch
        config_paths: List of config file paths/patterns to include (e.g., ["config_files/", "*.yml", "*.properties"])
        gitlab_token: Optional GitLab token for authentication
        
    Returns:
        True if successful, False otherwise
    """
    temp_dir = None
    try:
        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix="git_config_branch_")
        logger.info(f"Creating config-only branch {new_branch_name} from {main_branch}")
        logger.info(f"Config paths: {config_paths}")
        
        # Setup authentication
        auth_url = setup_git_auth(repo_url, gitlab_token)
        
        # Initialize empty repo
        logger.info(f"Initializing sparse checkout in: {temp_dir}")
        repo = git.Repo.init(temp_dir)
        
        # Add remote
        origin = repo.create_remote('origin', auth_url)
        
        # Enable sparse checkout
        with repo.config_writer() as config:
            config.set_value('core', 'sparseCheckout', 'true')
        
        # Write sparse-checkout patterns
        sparse_checkout_file = Path(temp_dir) / '.git' / 'info' / 'sparse-checkout'
        sparse_checkout_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(sparse_checkout_file, 'w') as f:
            for path in config_paths:
                f.write(f"{path}\n")
        
        logger.info(f"Sparse checkout configured for: {config_paths}")
        
        # Fetch only the main branch with depth=1 (shallow clone)
        logger.info(f"Fetching {main_branch} (shallow, config files only)...")
        origin.fetch(main_branch, depth=1)
        
        # Checkout the main branch
        repo.git.checkout(f'origin/{main_branch}')
        
        # Create new branch
        logger.info(f"Creating new branch: {new_branch_name}")
        new_branch = repo.create_head(new_branch_name)
        new_branch.checkout()
        
        # Push the new branch to remote
        logger.info(f"Pushing config-only branch {new_branch_name} to remote")
        repo.git.push('--set-upstream', 'origin', new_branch_name)
        
        logger.info(f"✅ Successfully created config-only branch {new_branch_name}")
        return True
        
    except GitCommandError as e:
        logger.error(f"Git error creating config-only branch {new_branch_name}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error creating config-only branch {new_branch_name}: {e}")
        return False
    finally:
        # Cleanup temporary directory
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                logger.info(f"Cleaned up temp directory: {temp_dir}")
            except Exception as e:
                logger.warning(f"Failed to cleanup temp directory {temp_dir}: {e}")


def list_branches_by_pattern(
    repo_url: str,
    pattern: str,
    gitlab_token: Optional[str] = None
) -> List[str]:
    """
    List all branches matching a specific pattern.
    
    Args:
        repo_url: Repository URL
        pattern: Pattern to match (e.g., "drift_prod_*")
        gitlab_token: Optional GitLab token for authentication
        
    Returns:
        List of branch names matching the pattern
    """
    temp_dir = None
    try:
        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix="git_list_")
        
        # Setup authentication
        auth_url = setup_git_auth(repo_url, gitlab_token)
        
        # Clone with minimal depth
        logger.info(f"Listing branches matching pattern: {pattern}")
        repo = git.Repo.clone_from(auth_url, temp_dir, depth=1, single_branch=False, no_checkout=True)
        
        # Fetch remote refs
        repo.remotes.origin.fetch()
        
        # Get all remote branches
        remote_branches = [ref.name.replace('origin/', '') for ref in repo.remotes.origin.refs]
        
        # Filter by pattern (simple prefix matching)
        pattern_prefix = pattern.replace('*', '')
        matching_branches = [b for b in remote_branches if b.startswith(pattern_prefix)]
        
        logger.info(f"Found {len(matching_branches)} branches matching {pattern}")
        return sorted(matching_branches)
        
    except Exception as e:
        logger.error(f"Error listing branches with pattern {pattern}: {e}")
        return []
    finally:
        # Cleanup temporary directory
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                logger.warning(f"Failed to cleanup temp directory {temp_dir}: {e}")


def delete_remote_branch(
    repo_url: str,
    branch_name: str,
    gitlab_token: Optional[str] = None
) -> bool:
    """
    Delete a branch from the remote repository.
    
    Args:
        repo_url: Repository URL
        branch_name: Branch name to delete
        gitlab_token: Optional GitLab token for authentication
        
    Returns:
        True if successful, False otherwise
    """
    temp_dir = None
    try:
        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix="git_delete_")
        
        # Setup authentication
        auth_url = setup_git_auth(repo_url, gitlab_token)
        
        # Clone repository (minimal)
        logger.info(f"Deleting remote branch: {branch_name}")
        repo = git.Repo.clone_from(auth_url, temp_dir, depth=1, single_branch=False, no_checkout=True)
        
        # Delete remote branch
        repo.git.push('origin', '--delete', branch_name)
        
        logger.info(f"✅ Successfully deleted branch {branch_name}")
        return True
        
    except GitCommandError as e:
        logger.error(f"Git error deleting branch {branch_name}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error deleting branch {branch_name}: {e}")
        return False
    finally:
        # Cleanup temporary directory
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                logger.warning(f"Failed to cleanup temp directory {temp_dir}: {e}")


def validate_git_credentials() -> bool:
    """
    Validate that Git credentials are configured.
    
    Returns:
        True if credentials are available, False otherwise
    """
    gitlab_token = os.getenv('GITLAB_TOKEN')
    gitlab_username = os.getenv('GITLAB_USERNAME')
    gitlab_password = os.getenv('GITLAB_PASSWORD')
    
    has_token = bool(gitlab_token)
    has_credentials = bool(gitlab_username and gitlab_password)
    
    return has_token or has_credentials

