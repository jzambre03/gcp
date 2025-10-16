#!/usr/bin/env python3
"""
Golden Config AI - Multi-Agent System Main Server

This server orchestrates the complete multi-agent validation workflow:
- Supervisor Agent coordinates the pipeline
- Config Collector Agent fetches Git diffs
- Diff Policy Engine Agent analyzes with AI

Runs on localhost:3000 for easy access.
"""

import uvicorn
import json
import os
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, field_validator

# Strands agent system imports
from shared.config import Config
from Agents.Supervisor.supervisor_agent import run_validation


# Setup templates directory
templates_dir = Path(__file__).parent / "api" / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

# Initialize FastAPI app
app = FastAPI(
    title="Golden Config AI - Multi-Agent System",
    description="Complete Configuration Drift Analysis with Supervisor + Worker Agents",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Load default values from environment
config = Config()


# Default config file paths for sparse checkout (config-only branches)
# These patterns match what drift_v1.py classifies as "config" files (line 63)
# Excludes .json and .xml as per user request
DEFAULT_CONFIG_PATHS = [
    "*.yml",                   # YAML config files
    "*.yaml",                  # YAML config files
    "*.properties",            # Properties files
    "*.toml",                  # TOML config files
    "*.ini",                   # INI config files
    "*.cfg",                   # Configuration files
    "*.conf",                  # Configuration files
    "*.config",                # Configuration files
    "Dockerfile",              # Docker configuration
    "docker-compose.yml",      # Docker Compose
    ".env.example",            # Environment template
    # Build files (also analyzed for config changes)
    "pom.xml",                 # Maven build file
    "build.gradle",            # Gradle build file
    "build.gradle.kts",        # Gradle Kotlin build file
    "settings.gradle",         # Gradle settings
    "settings.gradle.kts",     # Gradle Kotlin settings
    "package.json",            # NPM package file
    "requirements.txt",        # Python requirements
    "pyproject.toml",          # Python project file
    "go.mod",                  # Go module file
]

# Service Configuration
SERVICES_CONFIG = {
    "cxp_ordering_services": {
        "name": "CXP Ordering Services",
        "repo_url": "https://gitlab.verizon.com/saja9l7/cxp-ordering-services.git",
        "main_branch": "main",
        "environments": ["prod", "dev", "qa", "staging"],
        "config_paths": DEFAULT_CONFIG_PATHS  # Can be customized per service
    },
    "cxp_credit_services": {
        "name": "CXP Credit Services",
        "repo_url": "https://gitlab.verizon.com/saja9l7/cxp-credit-services.git",
        "main_branch": "main",
        "environments": ["prod", "dev", "qa", "staging"],
        "config_paths": DEFAULT_CONFIG_PATHS
    },
    "cxp_config_properties": {
        "name": "CXP Config Properties",
        "repo_url": "https://gitlab.verizon.com/saja9l7/cxp-config-properties.git",
        "main_branch": "main",
        "environments": ["prod", "dev", "qa", "staging"],
        "config_paths": DEFAULT_CONFIG_PATHS
    }
}

print(f"🏢 Services Configured:")
for service_id, config in SERVICES_CONFIG.items():
    print(f"   {service_id}: {config['name']}")
    print(f"      Repo: {config['repo_url']}")
    print(f"      Main Branch: {config['main_branch']}")
    print(f"      Environments: {', '.join(config['environments'])}")
print()

# Set defaults from first service for backward compatibility
# Note: These are only used for legacy endpoints - each service has its own URL
DEFAULT_REPO_URL = os.getenv("DEFAULT_REPO_URL", list(SERVICES_CONFIG.values())[0]["repo_url"])
DEFAULT_MAIN_BRANCH = os.getenv("DEFAULT_MAIN_BRANCH", list(SERVICES_CONFIG.values())[0]["main_branch"])
DEFAULT_ENVIRONMENT = os.getenv("DEFAULT_ENVIRONMENT", "prod")

print(f"🔧 Legacy Default Configuration (from {list(SERVICES_CONFIG.keys())[0]}):")
print(f"   DEFAULT_REPO_URL: {DEFAULT_REPO_URL}")
print(f"   DEFAULT_MAIN_BRANCH: {DEFAULT_MAIN_BRANCH}")
print(f"   DEFAULT_ENVIRONMENT: {DEFAULT_ENVIRONMENT}")
print(f"   ⚠️  Note: Each service uses its own configured URL and environments")
print()

# Request models
class ValidationRequest(BaseModel):
    """Request for configuration drift validation"""
    repo_url: str = Field(
        default=DEFAULT_REPO_URL,
        description="GitLab repository URL (legacy default - each service has its own URL)"
    )
    main_branch: str = Field(
        default=DEFAULT_MAIN_BRANCH,
        description="Main branch name (source of current configs)"
    )
    environment: str = Field(
        default=DEFAULT_ENVIRONMENT,
        description="Environment to validate (prod, dev, qa, staging)"
    )
    target_folder: str = Field(
        default="",
        description="Optional: specific folder to analyze (empty = entire repo)"
    )
    project_id: str = Field(
        default="config-validation",
        description="Project identifier"
    )
    mr_iid: str = Field(
        default="auto",
        description="Merge request ID or validation identifier"
    )
    
    @field_validator('repo_url')
    @classmethod
    def validate_repo_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('repo_url must be a valid HTTP/HTTPS URL')
        return v


class QuickAnalysisRequest(BaseModel):
    """Quick analysis with default settings"""
    pass


# Global state
latest_results: Optional[Dict[str, Any]] = None
validation_in_progress: bool = False


@app.get("/", response_class=HTMLResponse)
async def serve_ui(request: Request):
    """Serve the services overview dashboard"""
    return templates.TemplateResponse("overview.html", {"request": request})


@app.get("/branch-environment", response_class=HTMLResponse)
async def serve_branch_environment(request: Request):
    """Serve the branch & environment tracking page"""
    print("🌿 Serving Branch & Environment tracking page")
    print(f"🔍 Request URL: {request.url}")
    print(f"🔍 Query params: {dict(request.query_params)}")
    
    try:
        return templates.TemplateResponse("branch_env.html", {"request": request})
    except Exception as e:
        print(f"❌ Template error: {e}")
        print(f"📁 Templates directory: {templates_dir}")
        
        # Check if template file exists
        template_path = Path(__file__).parent / "api" / "templates" / "branch_env.html"
        print(f"🔍 Looking for template at: {template_path}")
        print(f"📄 File exists: {template_path.exists()}")
        
        # Fallback: serve the HTML content directly
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                content = f.read()
                print("✅ Successfully read template file directly")
                return HTMLResponse(content=content)
        except Exception as e2:
            print(f"❌ File read error: {e2}")
            # Return a basic HTML page as last resort
            return HTMLResponse(content=f"""
            <!DOCTYPE html>
            <html>
            <head><title>Branch Environment - Error</title></head>
            <body>
                <h1>Branch Environment Page</h1>
                <p>Error loading page: {str(e2)}</p>
                <p>Template path: {template_path}</p>
                <button onclick="window.history.back()">← Back</button>
            </body>
            </html>
            """)


# Legacy route removed - use service-specific dashboards instead
# Each service now has its own dashboard at /service/{service_id}


@app.get("/api/info")
async def api_info():
    """API information endpoint"""
    return {
        "service": "Golden Config AI - Multi-Agent System",
        "version": "2.0.0",
        "status": "running",
        "architecture": "supervisor_orchestration",
        "agents": {
            "supervisor": "Orchestrates the validation workflow",
            "config_collector": "Fetches Git diffs and analyzes changes",
            "diff_policy_engine": "AI-powered drift analysis and policy validation"
        },
        "communication": "file_based",
        "legacy_default_repo": DEFAULT_REPO_URL,
        "legacy_default_config": {
            "main_branch": DEFAULT_MAIN_BRANCH,
            "environment": DEFAULT_ENVIRONMENT
        },
        "note": "Each service has its own configured repository and environments",
        "endpoints": {
            "ui": "GET /",
            "branch_environment": "GET /branch-environment",
            "validate": "POST /api/validate",
            "quick_analyze": "POST /api/analyze/quick",
            "latest_results": "GET /api/latest-results",
            "validation_status": "GET /api/validation-status",
            "config": "GET /api/config",
            "llm_output": "GET /api/llm-output",
            "health": "GET /health"
        }
    }


@app.get("/api/validation-status")
async def validation_status():
    """Check if validation is in progress"""
    global validation_in_progress
    
    return {
        "in_progress": validation_in_progress,
        "has_results": latest_results is not None,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.post("/api/validate")
async def validate_configuration(request: ValidationRequest, background_tasks: BackgroundTasks):
    """
    Run complete multi-agent validation workflow.
    
    This orchestrates:
    1. Supervisor Agent - Creates validation run and coordinates workflow
    2. Config Collector Agent - Fetches Git diffs from repository
    3. Diff Policy Engine Agent - AI-powered drift analysis
    
    Returns file paths to analysis results.
    """
    global validation_in_progress, latest_results
    
    if validation_in_progress:
        raise HTTPException(
            status_code=409,
            detail="Validation already in progress. Please wait for completion."
        )
    
    print("=" * 80)
    print("🚀 MULTI-AGENT VALIDATION REQUEST")
    print("=" * 80)
    print(f"📦 Repository: {request.repo_url}")
    print(f"🌿 Main Branch: {request.main_branch}")
    print(f"🌍 Environment: {request.environment}")
    print(f"📁 Target Folder: {request.target_folder or 'entire repository'}")
    print(f"🆔 Project ID: {request.project_id}")
    print(f"🔢 MR/ID: {request.mr_iid}")
    print("=" * 80)
    
    try:
        validation_in_progress = True
        start_time = datetime.now()
        
        # Generate MR ID if auto
        mr_iid = request.mr_iid
        if mr_iid == "auto":
            mr_iid = f"val_{int(datetime.now().timestamp())}"
        
        print("\n🤖 Starting Supervisor Agent orchestration...")
        print("   ├─ Supervisor Agent: Coordinates workflow")
        print("   ├─ Config Collector Agent: Fetches Git diffs")
        print("   └─ Diff Policy Engine Agent: AI-powered analysis")
        print()
        
        # Run validation through supervisor
        result = run_validation(
            project_id=request.project_id,
            mr_iid=mr_iid,
            repo_url=request.repo_url,
            main_branch=request.main_branch,
            environment=request.environment,
            target_folder=request.target_folder
        )
        
        # Calculate execution time
        execution_time = (datetime.now() - start_time).total_seconds()
        
        print("\n" + "=" * 80)
        print("✅ VALIDATION COMPLETED")
        print("=" * 80)
        print(f"⏱️  Execution Time: {execution_time:.2f}s")
        print(f"🆔 Run ID: {result.get('run_id', 'N/A')}")
        print(f"📊 Verdict: {result.get('verdict', 'N/A')}")
        print("=" * 80)
        
        # Try to load enhanced analysis data if available
        enhanced_data = None
        try:
            # Look for the enhanced analysis file in the result
            if "data" in result and "file_paths" in result["data"]:
                enhanced_file = result["data"]["file_paths"].get("enhanced_analysis")
                if enhanced_file and Path(enhanced_file).exists():
                    with open(enhanced_file, 'r', encoding='utf-8') as f:
                        enhanced_data = json.load(f)
                    print(f"✅ Loaded enhanced analysis data from: {enhanced_file}")
        except Exception as e:
            print(f"⚠️ Could not load enhanced analysis data: {e}")
        
        # Prepare response with enhanced data if available
        validation_result = result
        if enhanced_data:
            # Merge enhanced data into validation result
            validation_result = {
                **result,
                "enhanced_data": enhanced_data,
                "clusters": enhanced_data.get("clusters", []),
                "analyzed_deltas": enhanced_data.get("analyzed_deltas_with_ai", []),
                "total_clusters": len(enhanced_data.get("clusters", [])),
                "policy_violations": enhanced_data.get("policy_violations", []),
                "policy_violations_count": len(enhanced_data.get("policy_violations", [])),
                "overall_risk_level": enhanced_data.get("overall_risk_level", "unknown"),
                "verdict": enhanced_data.get("verdict", "UNKNOWN"),
                "environment": enhanced_data.get("environment", "unknown"),
                "critical_violations": len([v for v in enhanced_data.get("policy_violations", []) if v.get('severity') == 'critical']),
                "high_violations": len([v for v in enhanced_data.get("policy_violations", []) if v.get('severity') == 'high'])
            }
        
        response = {
            "status": "success",
            "architecture": "multi_agent_supervisor",
            "agents_used": ["supervisor", "config_collector", "diff_policy_engine"],
            "communication_method": "file_based",
            "validation_result": validation_result,
            "execution_time_seconds": execution_time,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_params": {
                "repo_url": request.repo_url,
                "main_branch": request.main_branch,
                "environment": request.environment,
                "target_folder": request.target_folder or "/"
            }
        }
        
        latest_results = response
        
        return response
        
    except Exception as e:
        print("\n" + "=" * 80)
        print("❌ VALIDATION FAILED")
        print("=" * 80)
        print(f"Error: {str(e)}")
        print("=" * 80)
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")
    
    finally:
        validation_in_progress = False


@app.post("/api/analyze/quick")
async def quick_analyze(request: QuickAnalysisRequest):
    """
    Quick analysis with default settings from environment variables.
    
    This is a convenience endpoint that uses predefined repository and main branch from .env
    """
    print("🚀 Quick Analysis Request (using defaults from .env)")
    
    default_request = ValidationRequest(
        repo_url=DEFAULT_REPO_URL,
        main_branch=DEFAULT_MAIN_BRANCH,
        environment=DEFAULT_ENVIRONMENT,
        target_folder="",
        project_id="quick_analysis",
        mr_iid="quick_analysis"
    )
    
    # Use background tasks to avoid timeout
    from fastapi import BackgroundTasks
    background_tasks = BackgroundTasks()
    
    return await validate_configuration(default_request, background_tasks)


@app.get("/api/latest-results")
async def get_latest_results():
    """Get the latest validation results"""
    if latest_results:
        return latest_results
    else:
        raise HTTPException(status_code=404, detail="No validation results available yet")


@app.get("/api/sample-data")
async def get_sample_data():
    """
    Trigger a quick analysis for sample data.
    This is for UI compatibility with the old agent_analysis_server.
    """
    return await quick_analyze(QuickAnalysisRequest())


@app.post("/api/analyze/agent")
async def analyze_agent_compat(request: Dict[str, Any]):
    """
    Compatibility endpoint for UI that expects /api/analyze/agent.
    Maps to the new validation endpoint.
    """
    print("🔄 Legacy endpoint called (/api/analyze/agent), redirecting to new validation...")
    
    validation_request = ValidationRequest(
        repo_url=request.get("repo_url", DEFAULT_REPO_URL),
        main_branch=request.get("main_branch", DEFAULT_MAIN_BRANCH),
        environment=request.get("environment", DEFAULT_ENVIRONMENT),
        target_folder=request.get("target_folder", ""),
        project_id=request.get("project_id", "config-validation"),
        mr_iid=request.get("mr_iid", "auto")
    )
    
    from fastapi import BackgroundTasks
    background_tasks = BackgroundTasks()
    
    return await validate_configuration(validation_request, background_tasks)


@app.get("/api/agent-status")
async def agent_status():
    """Check agent system status"""
    try:
        config = Config()
        return {
            "status": "initialized",
            "architecture": "multi_agent_supervisor",
            "agents": {
                "supervisor": {
                    "status": "ready",
                    "description": "Orchestrates validation workflow",
                    "model": config.bedrock_model_id
                },
                "config_collector": {
                    "status": "ready",
                    "description": "Fetches Git diffs",
                    "model": config.bedrock_worker_model_id
                },
                "diff_policy_engine": {
                    "status": "ready",
                    "description": "AI-powered drift analysis",
                    "model": config.bedrock_worker_model_id
                }
            },
            "communication": "file_based",
            "output_location": "config_data/",
            "message": "All agents ready for validation"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": "Agent initialization failed"
        }


@app.get("/api/config")
async def get_config():
    """Get legacy environment configuration for UI"""
    return {
        "legacy_repo_url": DEFAULT_REPO_URL,
        "legacy_main_branch": DEFAULT_MAIN_BRANCH,
        "legacy_environment": DEFAULT_ENVIRONMENT,
        "note": "These are legacy defaults - each service has its own configured repository and environments",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.get("/api/llm-output")
async def get_llm_output():
    """Get the latest LLM output in adjudicator format"""
    import glob
    
    llm_output_files = sorted(glob.glob("config_data/llm_output/llm_output_*.json"), reverse=True)
    
    if llm_output_files:
        try:
            with open(llm_output_files[0], 'r', encoding='utf-8') as f:
                llm_output = json.load(f)
            
            return {
                "status": "success",
                "file_path": llm_output_files[0],
                "data": llm_output
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to load LLM output: {str(e)}")
    else:
        raise HTTPException(status_code=404, detail="No LLM output files available yet")


@app.get("/api/services")
async def get_services():
    """Get configured services with their status"""
    services = []
    
    for service_id, config in SERVICES_CONFIG.items():
        # Get last validation for this service
        last_result = get_last_service_result(service_id)
        
        # Determine status based on result
        status = "healthy"
        issues_count = 0
        
        if last_result:
            # Check if there are any policy violations or issues
            if "enhanced_data" in last_result:
                enhanced = last_result["enhanced_data"]
                issues_count = enhanced.get("policy_violations_count", 0)
                if issues_count > 0:
                    status = "warning" if enhanced.get("overall_risk_level") in ["medium", "high"] else "healthy"
                else:
                    status = "healthy"
            elif "validation_result" in last_result:
                # Check validation result for issues
                val_result = last_result["validation_result"]
                if val_result.get("verdict") == "FAIL":
                    status = "warning"
                    issues_count = 1  # At least one issue if failed
        
        services.append({
            "id": service_id,
            "name": config["name"],
            "status": status,
            "last_check": last_result.get("timestamp") if last_result else None,
            "issues": issues_count,
            "repo_url": config["repo_url"],
            "main_branch": config["main_branch"],
            "environments": config["environments"],
            "total_environments": len(config["environments"])
        })
    
    return {
        "services": services,
        "total_services": len(services),
        "active_issues": sum(s["issues"] for s in services),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.post("/api/services/{service_id}/analyze")
async def analyze_service_legacy(service_id: str, background_tasks: BackgroundTasks):
    """Legacy endpoint for backward compatibility - defaults to 'prod' environment"""
    return await analyze_service(service_id, "prod", background_tasks)


@app.post("/api/services/{service_id}/analyze/{environment}")
async def analyze_service(service_id: str, environment: str, background_tasks: BackgroundTasks):
    """Analyze specific service for a specific environment using dynamic branch creation"""
    if service_id not in SERVICES_CONFIG:
        raise HTTPException(404, f"Service {service_id} not found")
    
    config = SERVICES_CONFIG[service_id]
    
    # Validate environment
    if environment not in config["environments"]:
        raise HTTPException(400, f"Invalid environment '{environment}'. Must be one of: {config['environments']}")
    
    print("=" * 80)
    print(f"🚀 SERVICE-SPECIFIC ANALYSIS REQUEST")
    print("=" * 80)
    print(f"🆔 Service ID: {service_id}")
    print(f"📦 Repository: {config['repo_url']}")
    print(f"🌿 Main Branch: {config['main_branch']}")
    print(f"🌍 Environment: {environment}")
    print("=" * 80)
    
    # Use ValidationRequest with service-specific config
    request = ValidationRequest(
        repo_url=config["repo_url"],
        main_branch=config["main_branch"],
        environment=environment,
        target_folder="",
        project_id=f"{service_id}_{environment}",
        mr_iid=f"{service_id}_{environment}_analysis_{int(datetime.now().timestamp())}"
    )
    
    # Call validation function
    result = await validate_configuration(request, background_tasks)
    
    # Store service-specific result for future reference
    store_service_result(service_id, environment, result)
    
    return result


@app.get("/run/{run_id}", response_class=HTMLResponse)
async def view_run_details(request: Request, run_id: str):
    """
    View specific analysis run details in a new tab
    
    Shows drift analysis results for a specific run ID.
    This opens in a new browser tab/window for detailed review.
    """
    # Extract service_id from run_id (format: run_YYYYMMDD_HHMMSS_service_env_analysis_timestamp)
    # Example: run_20251015_185827_cxp_credit_services_prod_analysis_1760569065
    try:
        # Split by '_' but need to be smarter about service names with underscores
        parts = run_id.split('_')
        print(f"🔍 BACKEND: Parsing run_id '{run_id}' -> parts: {parts}")
        if len(parts) >= 7:  # run_20251015_185827_cxp_credit_services_prod_analysis_1760569065
                # Service name is between parts[3] and the environment (prod)
                # parts[0] = "run"
                # parts[1] = "20251015" (date)
                # parts[2] = "185827" (time)
                # parts[3:] = service name until environment
                env_positions = []
                for i, part in enumerate(parts):
                    if part in ['prod', 'dev', 'qa', 'staging']:
                        env_positions.append(i)
                
                if env_positions:
                    env_pos = env_positions[0]
                    # Service name is from parts[3] to env_pos-1 (skip run, date, time)
                    service_parts = parts[3:env_pos]
                    service_id = '_'.join(service_parts)  # cxp_credit_services
                    
                    print(f"🔍 BACKEND: Environment found at position {env_pos}, service_parts: {service_parts}")
                    print(f"🔍 Extracted service_id: '{service_id}' from run_id: '{run_id}'")
                
                from fastapi.responses import RedirectResponse
                return RedirectResponse(url=f"/branch-environment?id={service_id}&run_id={run_id}&tab=deployment", status_code=301)
    except:
        pass
    
    # Fallback: redirect without service_id, let frontend handle it
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"/branch-environment?run_id={run_id}&tab=deployment", status_code=301)


@app.get("/service/{service_id}", response_class=HTMLResponse)
async def service_detail(request: Request, service_id: str):
    """
    [DEPRECATED] Service-specific dashboard
    
    This endpoint is deprecated. All functionality has been moved to the 
    Branch & Environment page's "Drift Analysis" tab for better UX.
    
    Redirecting to: /branch-environment?id={service_id}&tab=deployment
    """
    if service_id not in SERVICES_CONFIG:
        raise HTTPException(404, f"Service {service_id} not found")
    
    # Redirect to Branch & Environment page with Drift Analysis tab
    # This provides the same functionality without a separate page
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"/branch-environment?id={service_id}&tab=deployment", status_code=301)


@app.get("/api/services/{service_id}/llm-output")
async def get_service_llm_output(service_id: str):
    """Get LLM output data for a specific service (for React dashboard)"""
    if service_id not in SERVICES_CONFIG:
        raise HTTPException(404, f"Service {service_id} not found")
    
    # Get the last result for this service
    last_result = get_last_service_result(service_id)
    
    if not last_result:
        raise HTTPException(
            status_code=404,
            detail=f"No analysis results available for {service_id}. Run analysis first."
        )
    
    # Extract validation_result
    result_data = last_result.get("validation_result", last_result)
    
    # Try to load the LLM output file if path is provided
    llm_output_path = result_data.get("llm_output_path")
    if llm_output_path and Path(llm_output_path).exists():
        try:
            with open(llm_output_path, 'r', encoding='utf-8') as f:
                llm_data = json.load(f)
                return {
                    "status": "success",
                    "data": llm_data,
                    "service_id": service_id,
                    "timestamp": last_result.get("timestamp")
                }
        except Exception as e:
            print(f"⚠️ Could not load LLM output file for {service_id}: {e}")
    
    # Fallback: try to find LLM output file in the file_paths
    file_paths = result_data.get("file_paths", {})
    for key in ["llm_output", "enhanced_analysis", "analyzed_deltas"]:
        file_path = file_paths.get(key)
        if file_path and Path(file_path).exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    llm_data = json.load(f)
                    return {
                        "status": "success",
                        "data": llm_data,
                        "service_id": service_id,
                        "timestamp": last_result.get("timestamp")
                    }
            except Exception as e:
                print(f"⚠️ Could not load file {file_path}: {e}")
    
    # If no LLM output file found, return error
    raise HTTPException(
        status_code=404,
        detail=f"LLM output data not found for {service_id}"
    )


def get_last_service_result(service_id: str, environment: Optional[str] = None):
    """
    Get most recent validation result for a service.
    
    Args:
        service_id: Service identifier
        environment: Optional environment name. If None, returns latest from any environment.
        
    Returns:
        Latest validation result or None
    """
    # First check in-memory latest_results
    if latest_results:
        req_params = latest_results.get("request_params", {})
        # Check if it matches service_id (and environment if specified)
        project_id = req_params.get("project_id", "")
        if project_id.startswith(service_id):
            if environment is None or req_params.get("environment") == environment:
                return latest_results
    
    # Then check stored files
    service_results_dir = Path("config_data") / "service_results" / service_id
    if not service_results_dir.exists():
        return None
    
    # If environment specified, look only in that environment's directory
    if environment:
        env_dir = service_results_dir / environment
        if env_dir.exists():
            result_files = sorted(env_dir.glob("validation_*.json"), reverse=True)
            if result_files:
                try:
                    with open(result_files[0], 'r', encoding='utf-8') as f:
                        stored_data = json.load(f)
                        print(f"✅ Loaded stored result for {service_id}/{environment} from: {result_files[0]}")
                        return stored_data.get("result")
                except Exception as e:
                    print(f"⚠️ Could not load stored result for {service_id}/{environment}: {e}")
    else:
        # No environment specified - find most recent from any environment
        all_result_files = []
        for env_dir in service_results_dir.iterdir():
            if env_dir.is_dir():
                all_result_files.extend(env_dir.glob("validation_*.json"))
        
        if all_result_files:
            # Sort by modification time to get the most recent
            most_recent = max(all_result_files, key=lambda p: p.stat().st_mtime)
            try:
                with open(most_recent, 'r', encoding='utf-8') as f:
                    stored_data = json.load(f)
                    print(f"✅ Loaded stored result for {service_id} from: {most_recent}")
                    return stored_data.get("result")
            except Exception as e:
                print(f"⚠️ Could not load stored result for {service_id}: {e}")
    
    return None


def store_service_result(service_id: str, environment: str, result: dict):
    """Store validation results with service and environment context"""
    global latest_results
    latest_results = result
    
    # Store to files for persistence (organized by environment)
    service_results_dir = Path("config_data") / "service_results" / service_id / environment
    service_results_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_file = service_results_dir / f"validation_{timestamp}.json"
    
    try:
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump({
                "service_id": service_id,
                "environment": environment,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "result": result
            }, f, indent=2, default=str)
        
        print(f"✅ Stored result for {service_id}/{environment} to: {result_file}")
        
        # NEW: Save to run history for UI display
        save_run_history(service_id, environment, {
            "validation_result": result,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        # Keep only the 5 most recent results per service/environment
        cleanup_old_results(service_results_dir, keep_count=5)
        
    except Exception as e:
        print(f"⚠️ Could not store result for {service_id}/{environment}: {e}")


def cleanup_old_results(service_dir: Path, keep_count: int = 5):
    """Clean up old result files, keeping only the most recent ones"""
    try:
        result_files = sorted(service_dir.glob("validation_*.json"), reverse=True)
        if len(result_files) > keep_count:
            for old_file in result_files[keep_count:]:
                old_file.unlink()
                print(f"🗑️ Cleaned up old result file: {old_file.name}")
    except Exception as e:
        print(f"⚠️ Could not cleanup old results: {e}")


def save_run_history(service_id: str, environment: str, run_data: dict):
    """
    Save run metadata to history file for displaying in UI.
    
    Args:
        service_id: Service identifier
        environment: Environment name
        run_data: Complete run data including metrics, branches, file paths
    """
    history_file = Path("config_data") / "service_results" / service_id / environment / "run_history.json"
    history_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing history
    history = {"service_id": service_id, "environment": environment, "runs": []}
    if history_file.exists():
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except Exception as e:
            print(f"⚠️ Could not load existing history: {e}")
    
    # Extract run metadata from result
    # Handle nested structure: run_data.validation_result.validation_result
    result = run_data.get("validation_result", run_data)  # Gets outer result object
    validation_result = result.get("validation_result", result)  # Gets nested validation_result
    request_params = result.get("request_params", validation_result.get("request_params", {}))
    
    # Debug: Log what we're extracting
    print(f"🔍 Extracting run metadata:")
    print(f"   Run ID: {validation_result.get('run_id', 'NOT FOUND')}")
    print(f"   Verdict: {validation_result.get('verdict', 'NOT FOUND')}")
    print(f"   Files analyzed: {validation_result.get('files_analyzed', 'NOT FOUND')}")
    print(f"   Files with drift: {validation_result.get('files_with_drift', 'NOT FOUND')}")
    
    # Try to get actual branch names from golden_branch_tracker
    golden_branch_name = "N/A"
    drift_branch_name = "N/A"
    try:
        from shared.golden_branch_tracker import get_all_branches, get_active_golden_branch
        golden_branches, drift_branches = get_all_branches(service_id, environment)
        golden_branch_name = get_active_golden_branch(service_id, environment) or "N/A"
        drift_branch_name = drift_branches[0] if drift_branches else "N/A"
        print(f"   Golden branch (from tracker): {golden_branch_name}")
        print(f"   Drift branch (from tracker): {drift_branch_name}")
    except Exception as e:
        print(f"⚠️ Could not fetch branch names from tracker: {e}")
    
    run_metadata = {
        "run_id": validation_result.get("run_id", "unknown"),
        "timestamp": run_data.get("timestamp", datetime.now(timezone.utc).isoformat()),
        "execution_time_seconds": validation_result.get("execution_time_ms", 0) / 1000 if validation_result.get("execution_time_ms") else 0,
        "verdict": validation_result.get("verdict", "UNKNOWN"),
        
        "branches": {
            "main_branch": request_params.get("main_branch", "unknown"),
            "golden_branch": validation_result.get("golden_branch", golden_branch_name),
            "drift_branch": validation_result.get("drift_branch", drift_branch_name)
        },
        
        "metrics": {
            "files_analyzed": validation_result.get("files_analyzed", 0),
            "files_with_drift": validation_result.get("files_with_drift", 0),
            "total_deltas": validation_result.get("total_deltas", 0),
            "policy_violations": validation_result.get("policy_violations_count", 0),
            "critical_violations": validation_result.get("critical_violations", 0),
            "high_violations": validation_result.get("high_violations", 0),
            "overall_risk_level": validation_result.get("overall_risk_level", "unknown")
        },
        
        "file_paths": validation_result.get("file_paths", {}),
        
        "summary": {
            "top_issues": [v.get("description", "") for v in (validation_result.get("policy_violations", []) or [])[:3]]
        }
    }
    
    # Add to beginning of runs list (newest first)
    history["runs"].insert(0, run_metadata)
    
    # Keep only last 50 runs to avoid file getting too large
    history["runs"] = history["runs"][:50]
    
    # Save updated history
    try:
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, default=str)
        print(f"✅ Saved run history for {service_id}/{environment}")
        print(f"   📁 File: {history_file}")
        print(f"   📊 Total runs: {len(history['runs'])}")
        print(f"   🆔 Latest run ID: {run_metadata.get('run_id', 'unknown')}")
        print(f"   ⚖️  Latest verdict: {run_metadata.get('verdict', 'unknown')}")
    except Exception as e:
        print(f"⚠️ Could not save run history: {e}")


@app.post("/api/services/{service_id}/import-result/{environment}")
async def import_service_result(service_id: str, environment: str, result_data: dict):
    """Import analysis result for a service/environment (useful for transferring results from other machines)"""
    if service_id not in SERVICES_CONFIG:
        raise HTTPException(404, f"Service {service_id} not found")
    
    config = SERVICES_CONFIG[service_id]
    if environment not in config["environments"]:
        raise HTTPException(400, f"Invalid environment '{environment}'. Must be one of: {config['environments']}")
    
    try:
        # Store the imported result
        store_service_result(service_id, environment, result_data)
        
        return {
            "status": "success",
            "message": f"Result imported successfully for {service_id}/{environment}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to import result: {str(e)}")


@app.get("/api/services/{service_id}/results")
async def get_service_results(service_id: str):
    """Get all stored results for a service"""
    if service_id not in SERVICES_CONFIG:
        raise HTTPException(404, f"Service {service_id} not found")
    
    service_results_dir = Path("config_data") / "service_results" / service_id
    results = []
    
    if service_results_dir.exists():
        result_files = sorted(service_results_dir.glob("validation_*.json"), reverse=True)
        for result_file in result_files:
            try:
                with open(result_file, 'r', encoding='utf-8') as f:
                    stored_data = json.load(f)
                    results.append({
                        "file_name": result_file.name,
                        "timestamp": stored_data.get("timestamp"),
                        "service_id": stored_data.get("service_id"),
                        "has_result": "result" in stored_data
                    })
            except Exception as e:
                print(f"⚠️ Could not read result file {result_file}: {e}")
    
    return {
        "service_id": service_id,
        "total_results": len(results),
        "results": results
    }


@app.post("/api/services/{service_id}/set-golden/{environment}")
async def set_golden_branch(service_id: str, environment: str, branch_name: Optional[str] = None):
    """
    Set a golden branch for a service and environment.
    If branch_name is not provided, creates a new golden branch from main.
    """
    if service_id not in SERVICES_CONFIG:
        raise HTTPException(404, f"Service {service_id} not found")
    
    config = SERVICES_CONFIG[service_id]
    if environment not in config["environments"]:
        raise HTTPException(400, f"Invalid environment '{environment}'. Must be one of: {config['environments']}")
    
    try:
        from shared.golden_branch_tracker import add_golden_branch
        from shared.git_operations import (
            generate_unique_branch_name, 
            create_config_only_branch,  # NEW: Config-only branch creation
            check_branch_exists
        )
        
        # If branch_name not provided, create new golden branch
        if not branch_name:
            branch_name = generate_unique_branch_name("golden", environment)
            
            # Create config-only branch from main (FAST - only config files)
            config_paths = config.get("config_paths", DEFAULT_CONFIG_PATHS)
            success = create_config_only_branch(
                repo_url=config["repo_url"],
                main_branch=config["main_branch"],
                new_branch_name=branch_name,
                config_paths=config_paths,
                gitlab_token=os.getenv('GITLAB_TOKEN')
            )
            
            if not success:
                raise HTTPException(500, f"Failed to create golden branch {branch_name}")
        else:
            # Validate that the provided branch exists
            if not check_branch_exists(config["repo_url"], branch_name, os.getenv('GITLAB_TOKEN')):
                raise HTTPException(404, f"Branch {branch_name} does not exist in repository")
        
        # Add to tracker
        add_golden_branch(service_id, environment, branch_name)
        
        return {
            "status": "success",
            "message": f"Golden branch set for {service_id}/{environment}",
            "branch_name": branch_name,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set golden branch: {str(e)}")


@app.post("/api/services/{service_id}/certify-selective/{environment}")
async def certify_selective_files(service_id: str, environment: str, request: Request):
    """
    Create a new golden branch with only selected files from drift branch.
    Rejected files are kept from the old golden branch.
    """
    if service_id not in SERVICES_CONFIG:
        raise HTTPException(404, f"Service {service_id} not found")
    
    config = SERVICES_CONFIG[service_id]
    if environment not in config["environments"]:
        raise HTTPException(400, f"Invalid environment '{environment}'. Must be one of: {config['environments']}")
    
    try:
        # Get approved files from request
        data = await request.json()
        approved_files = data.get("approved_files", [])
        
        if not approved_files:
            raise HTTPException(400, "No files selected for certification")
        
        from shared.golden_branch_tracker import get_active_golden_branch, get_active_drift_branch, add_golden_branch
        from shared.git_operations import (
            generate_unique_branch_name,
            create_selective_golden_branch
        )
        
        # Get current golden and drift branches
        old_golden_branch = get_active_golden_branch(service_id, environment)
        drift_branch = get_active_drift_branch(service_id, environment)
        
        if not old_golden_branch:
            raise HTTPException(404, f"No golden branch found for {service_id}/{environment}")
        
        if not drift_branch:
            raise HTTPException(404, f"No drift branch found for {service_id}/{environment}")
        
        # Generate new golden branch name
        new_golden_branch = generate_unique_branch_name("golden", environment)
        
        # Create new golden branch with selective files
        success = create_selective_golden_branch(
            repo_url=config["repo_url"],
            old_golden_branch=old_golden_branch,
            drift_branch=drift_branch,
            new_branch_name=new_golden_branch,
            approved_files=approved_files,
            config_paths=config.get("config_paths", DEFAULT_CONFIG_PATHS),
            gitlab_token=os.getenv('GITLAB_TOKEN')
        )
        
        if not success:
            raise HTTPException(500, f"Failed to create selective golden branch")
        
        # Add new golden branch to tracker
        add_golden_branch(service_id, environment, new_golden_branch)
        
        return {
            "status": "success",
            "message": f"Selective certification completed for {service_id}/{environment}",
            "golden_branch": new_golden_branch,
            "approved_files_count": len(approved_files),
            "approved_files": approved_files,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Selective certification failed: {str(e)}")


@app.get("/api/services/{service_id}/branches/{environment}")
async def get_service_branches(service_id: str, environment: str):
    """Get all golden and drift branches for a service and environment"""
    if service_id not in SERVICES_CONFIG:
        raise HTTPException(404, f"Service {service_id} not found")
    
    config = SERVICES_CONFIG[service_id]
    if environment not in config["environments"]:
        raise HTTPException(400, f"Invalid environment '{environment}'. Must be one of: {config['environments']}")
    
    try:
        from shared.golden_branch_tracker import get_all_branches, get_active_golden_branch
        
        golden_branches, drift_branches = get_all_branches(service_id, environment)
        active_golden = get_active_golden_branch(service_id, environment)
        
        return {
            "service_id": service_id,
            "environment": environment,
            "active_golden_branch": active_golden,
            "golden_branches": golden_branches,
            "drift_branches": drift_branches,
            "total_golden": len(golden_branches),
            "total_drift": len(drift_branches),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get branches: {str(e)}")


@app.get("/api/services/{service_id}/validate-golden/{environment}")
async def validate_golden_branch(service_id: str, environment: str):
    """Check if a golden branch exists for a service and environment"""
    if service_id not in SERVICES_CONFIG:
        raise HTTPException(404, f"Service {service_id} not found")
    
    config = SERVICES_CONFIG[service_id]
    if environment not in config["environments"]:
        raise HTTPException(400, f"Invalid environment '{environment}'. Must be one of: {config['environments']}")
    
    try:
        from shared.golden_branch_tracker import validate_golden_exists, get_active_golden_branch
        
        exists = validate_golden_exists(service_id, environment)
        active_branch = get_active_golden_branch(service_id, environment) if exists else None
        
        return {
            "service_id": service_id,
            "environment": environment,
            "golden_exists": exists,
            "active_golden_branch": active_branch,
            "message": "Golden branch found" if exists else "No golden branch found. Please create a golden baseline first.",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to validate golden branch: {str(e)}")

@app.delete("/api/services/{service_id}/revoke-golden/{environment}")
async def revoke_golden_branch(service_id: str, environment: str):
    """Revoke (delete) the active golden branch for a service and environment"""
    if service_id not in SERVICES_CONFIG:
        raise HTTPException(404, f"Service {service_id} not found")
    
    config = SERVICES_CONFIG[service_id]
    if environment not in config["environments"]:
        raise HTTPException(400, f"Invalid environment '{environment}'. Must be one of: {config['environments']}")
    
    try:
        from shared.golden_branch_tracker import validate_golden_exists, get_active_golden_branch, remove_golden_branch
        
        # Check if golden branch exists
        if not validate_golden_exists(service_id, environment):
            raise HTTPException(400, f"No golden branch found for {service_id}/{environment}")
        
        # Get the active golden branch
        active_branch = get_active_golden_branch(service_id, environment)
        
        # Remove the golden branch from tracking
        remove_golden_branch(service_id, environment, active_branch)
        
        print(f"✅ Revoked golden branch {active_branch} for {service_id}/{environment}")
        
        return {
            "service_id": service_id,
            "environment": environment,
            "revoked_branch": active_branch,
            "message": f"Golden branch {active_branch} has been revoked",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error revoking golden branch for {service_id}/{environment}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to revoke golden branch: {str(e)}")


@app.get("/api/services/{service_id}/run-history/{environment}")
async def get_run_history(service_id: str, environment: str):
    """Get run history for a specific service/environment"""
    if service_id not in SERVICES_CONFIG:
        raise HTTPException(404, f"Service {service_id} not found")
    
    config = SERVICES_CONFIG[service_id]
    if environment not in config["environments"]:
        raise HTTPException(400, f"Invalid environment '{environment}'. Must be one of: {config['environments']}")
    
    history_file = Path("config_data") / "service_results" / service_id / environment / "run_history.json"
    
    if not history_file.exists():
        return {
            "service_id": service_id,
            "environment": environment,
            "runs": []
        }
    
    try:
        with open(history_file, 'r', encoding='utf-8') as f:
            history = json.load(f)
        return history
    except Exception as e:
        raise HTTPException(500, f"Failed to load run history: {str(e)}")


@app.get("/api/services/{service_id}/run/{run_id}")
async def get_run_details(service_id: str, run_id: str):
    """Get detailed results for a specific run"""
    if service_id not in SERVICES_CONFIG:
        raise HTTPException(404, f"Service {service_id} not found")
    
    # Search for the run in all environments
    for env in SERVICES_CONFIG[service_id]["environments"]:
        history_file = Path("config_data") / "service_results" / service_id / env / "run_history.json"
        
        if history_file.exists():
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                
                # Find the specific run
                for run in history["runs"]:
                    if run["run_id"] == run_id:
                        # Try to load the detailed result file
                        result_file = run["file_paths"].get("stored_result")
                        if result_file and Path(result_file).exists():
                            with open(result_file, 'r', encoding='utf-8') as rf:
                                detailed_result = json.load(rf)
                            return detailed_result
                        else:
                            # Return the run metadata at least
                            return {"run": run, "environment": env}
            except Exception as e:
                print(f"⚠️ Error searching in {env}: {e}")
                continue
    
    raise HTTPException(404, f"Run {run_id} not found for service {service_id}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    
    return {
        "status": "healthy",
        "service": "Golden Config AI - Multi-Agent System",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "2.0.0",
        "architecture": "supervisor_orchestration",
        "validation_in_progress": validation_in_progress,
        "has_results": latest_results is not None
    }


def main():
    """Start the multi-agent validation server"""
    print("\n" + "=" * 80)
    print("🚀 GOLDEN CONFIG AI - MULTI-AGENT SYSTEM")
    print("=" * 80)
    print()
    print("🌐 Server URLs:")
    print(f"   Dashboard:  http://localhost:3000")
    print(f"   API Docs:   http://localhost:3000/docs")
    print(f"   Health:     http://localhost:3000/health")
    print()
    print("🤖 AGENT ARCHITECTURE:")
    print("   ┌─────────────────────────────────┐")
    print("   │     Supervisor Agent            │  ← Orchestrates workflow")
    print("   │  (Claude 3.5 Sonnet)            │")
    print("   └──────────┬──────────────────────┘")
    print("              │")
    print("              ├──► Config Collector Agent")
    print("              │    (Fetches Git diffs)")
    print("              │    (Claude 3 Haiku)")
    print("              │")
    print("              └──► Diff Policy Engine Agent")
    print("                   (AI-powered analysis)")
    print("                   (Claude 3 Haiku)")
    print()
    print("💾 Communication: File-Based")
    print("   ├─ Config Collector → config_data/drift_analysis/*.json")
    print("   ├─ Diff Engine     → config_data/diff_analysis/*.json")
    print("   └─ Supervisor      → config_data/reports/*.md")
    print()
    print("🎯 LEGACY DEFAULT CONFIGURATION (for backward compatibility):")
    print(f"   Repository: {DEFAULT_REPO_URL}")
    print(f"   Main Branch: {DEFAULT_MAIN_BRANCH}")
    print(f"   Environment: {DEFAULT_ENVIRONMENT}")
    print(f"   ⚠️  Note: Each service uses its own configured repository and environments")
    print()
    print("📚 ENDPOINTS:")
    print("   POST /api/validate          - Run full validation (custom params)")
    print("   POST /api/analyze/quick     - Quick analysis (default settings)")
    print("   POST /api/analyze/agent     - Legacy compatibility endpoint")
    print("   GET  /api/latest-results    - Get most recent validation results")
    print("   GET  /api/validation-status - Check if validation is running")
    print("   GET  /api/agent-status      - Check agent system status")
    print()
    print("🎮 USAGE:")
    print("   1. Open http://localhost:3000 in your browser")
    print("   2. Click 'Load Sample Data' or 'Analyze' to start validation")
    print("   3. Watch the multi-agent system coordinate the analysis")
    print("   4. Review comprehensive drift analysis results")
    print()
    print("✨ FEATURES:")
    print("   ✅ Complete Supervisor orchestration")
    print("   ✅ File-based inter-agent communication")
    print("   ✅ Real GitLab repository analysis")
    print("   ✅ AI-powered drift detection with enhanced prompts")
    print("   ✅ Comprehensive risk assessment")
    print("   ✅ Policy violation detection")
    print("   ✅ Actionable recommendations")
    print()
    print("🛑 Press Ctrl+C to stop")
    print("=" * 80)
    print()
    
    uvicorn.run(
        app,
        host="0.0.0.0",  # Listen on all interfaces
        port=3000,
        log_level="info"
    )


if __name__ == "__main__":
    main()