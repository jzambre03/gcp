"""
Golden Branch Tracker - Manages golden and drift branch metadata

This module tracks which golden and drift branches exist for each service and environment,
storing the data in a JSON file for persistence.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Path to the JSON file storing branch metadata
BRANCHES_FILE = Path(__file__).parent.parent / "config_data" / "golden_branches.json"

# Maximum number of branches to keep per environment
MAX_BRANCHES_PER_ENV = 10


def _load_branches_data() -> Dict:
    """Load branch metadata from JSON file."""
    if not BRANCHES_FILE.exists():
        logger.warning(f"Branches file not found: {BRANCHES_FILE}")
        return {}
    
    try:
        with open(BRANCHES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse branches JSON: {e}")
        return {}
    except Exception as e:
        logger.error(f"Failed to load branches data: {e}")
        return {}


def _save_branches_data(data: Dict) -> None:
    """Save branch metadata to JSON file."""
    try:
        # Ensure directory exists
        BRANCHES_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        with open(BRANCHES_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved branches data to {BRANCHES_FILE}")
    except Exception as e:
        logger.error(f"Failed to save branches data: {e}")
        raise


def _ensure_service_structure(data: Dict, service_id: str, environment: str) -> Dict:
    """Ensure the service and environment structure exists in data."""
    if service_id not in data:
        data[service_id] = {}
    
    if environment not in data[service_id]:
        data[service_id][environment] = {
            "golden_branches": [],
            "drift_branches": []
        }
    
    return data


def get_active_golden_branch(service_id: str, environment: str) -> Optional[str]:
    """
    Get the most recent (active) golden branch for a service and environment.
    
    Args:
        service_id: Service identifier (e.g., "cxp_ordering_services")
        environment: Environment name (e.g., "prod", "dev", "qa", "staging")
        
    Returns:
        Branch name (e.g., "golden_prod_20251015_143052") or None if not found
    """
    data = _load_branches_data()
    
    if service_id not in data:
        logger.warning(f"Service {service_id} not found in branches data")
        return None
    
    if environment not in data[service_id]:
        logger.warning(f"Environment {environment} not found for service {service_id}")
        return None
    
    golden_branches = data[service_id][environment].get("golden_branches", [])
    
    if not golden_branches:
        logger.warning(f"No golden branches found for {service_id}/{environment}")
        return None
    
    # Return the most recent (last in list)
    return golden_branches[-1]


def add_golden_branch(service_id: str, environment: str, branch_name: str) -> None:
    """
    Add a new golden branch for a service and environment.
    Keeps only the last MAX_BRANCHES_PER_ENV branches.
    
    Args:
        service_id: Service identifier
        environment: Environment name
        branch_name: Golden branch name (e.g., "golden_prod_20251015_143052")
    """
    data = _load_branches_data()
    data = _ensure_service_structure(data, service_id, environment)
    
    golden_branches = data[service_id][environment]["golden_branches"]
    
    # Add new branch
    golden_branches.append(branch_name)
    
    # Keep only last MAX_BRANCHES_PER_ENV
    if len(golden_branches) > MAX_BRANCHES_PER_ENV:
        removed = golden_branches[:-MAX_BRANCHES_PER_ENV]
        data[service_id][environment]["golden_branches"] = golden_branches[-MAX_BRANCHES_PER_ENV:]
        logger.info(f"Removed old golden branches for {service_id}/{environment}: {removed}")
    
    _save_branches_data(data)
    logger.info(f"Added golden branch {branch_name} for {service_id}/{environment}")


def add_drift_branch(service_id: str, environment: str, branch_name: str) -> None:
    """
    Add a new drift branch for a service and environment.
    Keeps only the last MAX_BRANCHES_PER_ENV branches.
    
    Args:
        service_id: Service identifier
        environment: Environment name
        branch_name: Drift branch name (e.g., "drift_prod_20251015_143052")
    """
    data = _load_branches_data()
    data = _ensure_service_structure(data, service_id, environment)
    
    drift_branches = data[service_id][environment]["drift_branches"]
    
    # Add new branch
    drift_branches.append(branch_name)
    
    # Keep only last MAX_BRANCHES_PER_ENV
    if len(drift_branches) > MAX_BRANCHES_PER_ENV:
        removed = drift_branches[:-MAX_BRANCHES_PER_ENV]
        data[service_id][environment]["drift_branches"] = drift_branches[-MAX_BRANCHES_PER_ENV:]
        logger.info(f"Removed old drift branches for {service_id}/{environment}: {removed}")
    
    _save_branches_data(data)
    logger.info(f"Added drift branch {branch_name} for {service_id}/{environment}")


def get_all_branches(service_id: str, environment: str) -> Tuple[List[str], List[str]]:
    """
    Get all golden and drift branches for a service and environment.
    
    Args:
        service_id: Service identifier
        environment: Environment name
        
    Returns:
        Tuple of (golden_branches, drift_branches)
    """
    data = _load_branches_data()
    
    if service_id not in data or environment not in data[service_id]:
        return ([], [])
    
    env_data = data[service_id][environment]
    golden_branches = env_data.get("golden_branches", [])
    drift_branches = env_data.get("drift_branches", [])
    
    return (golden_branches, drift_branches)


def validate_golden_exists(service_id: str, environment: str) -> bool:
    """
    Check if a golden branch exists for a service and environment.
    
    Args:
        service_id: Service identifier
        environment: Environment name
        
    Returns:
        True if golden branch exists, False otherwise
    """
    golden_branch = get_active_golden_branch(service_id, environment)
    return golden_branch is not None


def initialize_service(service_id: str, environments: List[str]) -> None:
    """
    Initialize branch tracking for a new service with its environments.
    
    Args:
        service_id: Service identifier
        environments: List of environment names (e.g., ["prod", "dev", "qa", "staging"])
    """
    data = _load_branches_data()
    
    if service_id not in data:
        data[service_id] = {}
    
    for env in environments:
        if env not in data[service_id]:
            data[service_id][env] = {
                "golden_branches": [],
                "drift_branches": []
            }
    
    _save_branches_data(data)
    logger.info(f"Initialized service {service_id} with environments: {environments}")


def get_all_services() -> Dict[str, Dict[str, Dict]]:
    """
    Get all services and their branch data.
    
    Returns:
        Complete branches data structure
    """
    return _load_branches_data()


def remove_branch(service_id: str, environment: str, branch_name: str, branch_type: str) -> bool:
    """
    Remove a specific branch from tracking.
    
    Args:
        service_id: Service identifier
        environment: Environment name
        branch_name: Branch name to remove
        branch_type: "golden" or "drift"
        
    Returns:
        True if removed, False if not found
    """
    data = _load_branches_data()
    
    if service_id not in data or environment not in data[service_id]:
        return False
    
    branch_list_key = f"{branch_type}_branches"
    branches = data[service_id][environment].get(branch_list_key, [])
    
    if branch_name in branches:
        branches.remove(branch_name)
        data[service_id][environment][branch_list_key] = branches
        _save_branches_data(data)
        logger.info(f"Removed {branch_type} branch {branch_name} for {service_id}/{environment}")
        return True
    
    return False


# Initialize the branches file if it doesn't exist
if not BRANCHES_FILE.exists():
    logger.info(f"Creating initial branches file at {BRANCHES_FILE}")
    BRANCHES_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(BRANCHES_FILE, 'w', encoding='utf-8') as f:
        json.dump({}, f, indent=2)

