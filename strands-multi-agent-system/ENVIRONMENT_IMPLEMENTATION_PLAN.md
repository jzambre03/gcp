# 🚀 Environment-Aware Analysis - Implementation Plan

## 📊 **OVERVIEW**

This document provides a step-by-step implementation plan to make your drift analysis system environment-aware, so that:
- Production drifts are assessed with maximum strictness
- Dev drifts are lenient for experimental changes
- QA/Staging drifts balance between the two
- Same change = different risk level based on target environment

---

## 🎯 **IMPLEMENTATION STRATEGY**

We'll implement this in **5 phases**, working from the API layer down to the AI prompt layer:

```
Phase 1: Service Configuration (main.py)
    ↓
Phase 2: API Endpoints (main.py)
    ↓
Phase 3: Supervisor Agent (supervisor_agent.py)
    ↓
Phase 4: Diff Engine Agent (diff_engine_agent.py)
    ↓
Phase 5: LLM Prompt Enhancement (llm_format_prompt.py)
```

**Total Estimated Time:** 2-3 hours
**Risk Level:** Low (backward compatible changes)
**Testing Required:** Yes (at each phase)

---

## 📋 **PHASE 1: SERVICE CONFIGURATION** (15 minutes)

### **Goal:** Add environment metadata to each service

### **File to Modify:** `strands-multi-agent-system/main.py`

### **Step 1.1: Update SERVICES_CONFIG**

**Current Structure (Lines 61-80):**
```python
SERVICES_CONFIG = {
    "cxp_ordering_services": {
        "name": "CXP Ordering Services",
        "repo_url": "https://gitlab.verizon.com/saja917/cxp-ordering-services.git",
        "golden_branch": "golden",
        "drift_branch": "drifted"
    },
    "cxp_credit_services": {
        "name": "CXP Credit Services",
        "repo_url": "https://gitlab.verizon.com/saja917/cxp-credit-services.git",
        "golden_branch": "golden",
        "drift_branch": "drifted"
    },
    "cxp_config_properties": {
        "name": "CXP Config Properties",
        "repo_url": "https://gitlab.verizon.com/saja917/cxp-config-properties.git",
        "golden_branch": "golden",
        "drift_branch": "drifted"
    }
}
```

**New Structure (ADD environment field):**
```python
SERVICES_CONFIG = {
    "cxp_ordering_services": {
        "name": "CXP Ordering Services",
        "repo_url": "https://gitlab.verizon.com/saja917/cxp-ordering-services.git",
        "golden_branch": "golden",
        "drift_branch": "drifted",
        "environment": "production"  # ← NEW: Specify target environment
    },
    "cxp_credit_services": {
        "name": "CXP Credit Services",
        "repo_url": "https://gitlab.verizon.com/saja917/cxp-credit-services.git",
        "golden_branch": "golden",
        "drift_branch": "drifted",
        "environment": "qa"  # ← NEW: QA environment
    },
    "cxp_config_properties": {
        "name": "CXP Config Properties",
        "repo_url": "https://gitlab.verizon.com/saja917/cxp-config-properties.git",
        "golden_branch": "golden",
        "drift_branch": "drifted",
        "environment": "dev"  # ← NEW: Dev environment
    }
}
```

### **Step 1.2: Add Environment Validation**

**Add after SERVICES_CONFIG definition:**
```python
# Validate environment values
VALID_ENVIRONMENTS = ["production", "staging", "qa", "dev"]

for service_id, config in SERVICES_CONFIG.items():
    env = config.get("environment", "production")
    if env not in VALID_ENVIRONMENTS:
        print(f"⚠️  Warning: Service {service_id} has invalid environment '{env}'. Defaulting to 'production'.")
        config["environment"] = "production"
```

### **✅ Phase 1 Verification:**
```bash
# Check that services have environment field
python3 -c "
from main import SERVICES_CONFIG
for sid, cfg in SERVICES_CONFIG.items():
    print(f'{sid}: {cfg.get(\"environment\", \"MISSING\")}')"
```

**Expected Output:**
```
cxp_ordering_services: production
cxp_credit_services: qa
cxp_config_properties: dev
```

---

## 📋 **PHASE 2: API ENDPOINTS** (20 minutes)

### **Goal:** Pass environment parameter through API to validation pipeline

### **File to Modify:** `strands-multi-agent-system/main.py`

### **Step 2.1: Update analyze_service Endpoint**

**Current Code (Lines ~395-450):**
```python
@app.post("/api/services/{service_id}/analyze")
async def analyze_service(service_id: str, background_tasks: BackgroundTasks):
    if service_id not in SERVICES_CONFIG:
        raise HTTPException(404, f"Service {service_id} not found")
    
    config = SERVICES_CONFIG[service_id]
    
    # Run validation
    result = run_validation(
        project_id=service_id,
        mr_iid=f"val_{int(datetime.now().timestamp())}",
        repo_url=config["repo_url"],
        golden_branch=config["golden_branch"],
        drift_branch=config["drift_branch"],
        target_folder=""
        # ❌ No environment parameter!
    )
```

**New Code (ADD environment parameter):**
```python
@app.post("/api/services/{service_id}/analyze")
async def analyze_service(service_id: str, background_tasks: BackgroundTasks):
    if service_id not in SERVICES_CONFIG:
        raise HTTPException(404, f"Service {service_id} not found")
    
    config = SERVICES_CONFIG[service_id]
    environment = config.get("environment", "production")  # ← NEW: Extract environment
    
    print(f"🌍 Analyzing {service_id} for environment: {environment.upper()}")  # ← NEW: Log
    
    # Run validation
    result = run_validation(
        project_id=service_id,
        mr_iid=f"val_{int(datetime.now().timestamp())}",
        repo_url=config["repo_url"],
        golden_branch=config["golden_branch"],
        drift_branch=config["drift_branch"],
        target_folder="",
        environment=environment  # ← NEW: Pass environment
    )
```

### **Step 2.2: Update ValidationRequest Model (Optional but Recommended)**

**Find ValidationRequest class (around line 100-120):**
```python
class ValidationRequest(BaseModel):
    repo_url: str = Field(..., description="GitLab repository URL")
    golden_branch: str = Field(..., description="Golden/reference branch")
    drift_branch: str = Field(..., description="Drift/comparison branch")
    target_folder: str = Field(default="", description="Optional subfolder to analyze")
    project_id: str = Field(default="default", description="Project identifier")
    mr_iid: str = Field(default="auto", description="Merge request or validation ID")
```

**Add environment field:**
```python
class ValidationRequest(BaseModel):
    repo_url: str = Field(..., description="GitLab repository URL")
    golden_branch: str = Field(..., description="Golden/reference branch")
    drift_branch: str = Field(..., description="Drift/comparison branch")
    target_folder: str = Field(default="", description="Optional subfolder to analyze")
    project_id: str = Field(default="default", description="Project identifier")
    mr_iid: str = Field(default="auto", description="Merge request or validation ID")
    environment: str = Field(default="production", description="Target environment (production/staging/qa/dev)")  # ← NEW
    
    @field_validator('environment')
    @classmethod
    def validate_environment(cls, v):
        valid = ["production", "staging", "qa", "dev"]
        if v not in valid:
            raise ValueError(f"Environment must be one of: {valid}")
        return v
```

### **Step 2.3: Update /api/validate Endpoint**

**Find validate_configuration function (around line 204-333):**
```python
@app.post("/api/validate")
async def validate_configuration(request: ValidationRequest, background_tasks: BackgroundTasks):
    # ...existing code...
    
    # Run validation through supervisor
    result = run_validation(
        project_id=request.project_id,
        mr_iid=mr_iid,
        repo_url=request.repo_url,
        golden_branch=request.golden_branch,
        drift_branch=request.drift_branch,
        target_folder=request.target_folder
        # ❌ Missing environment
    )
```

**Update to:**
```python
@app.post("/api/validate")
async def validate_configuration(request: ValidationRequest, background_tasks: BackgroundTasks):
    # ...existing code...
    
    environment = request.environment  # ← NEW: Extract from request
    
    print(f"🌍 Environment: {environment.upper()}")  # ← NEW: Log
    
    # Run validation through supervisor
    result = run_validation(
        project_id=request.project_id,
        mr_iid=mr_iid,
        repo_url=request.repo_url,
        golden_branch=request.golden_branch,
        drift_branch=request.drift_branch,
        target_folder=request.target_folder,
        environment=environment  # ← NEW: Pass environment
    )
```

### **✅ Phase 2 Verification:**
```bash
# Test that environment is logged
curl -X POST http://localhost:3000/api/services/cxp_ordering_services/analyze
# Check terminal output for: "🌍 Analyzing cxp_ordering_services for environment: PRODUCTION"
```

---

## 📋 **PHASE 3: SUPERVISOR AGENT** (15 minutes)

### **Goal:** Forward environment parameter through the orchestration layer

### **File to Modify:** `strands-multi-agent-system/Agents/Supervisor/supervisor_agent.py`

### **Step 3.1: Update run_validation() Signature**

**Current Signature (Line ~1150):**
```python
def run_validation(
    project_id: str,
    mr_iid: str,
    repo_url: str,
    golden_branch: str,
    drift_branch: str,
    target_folder: str = ""
) -> dict:
```

**New Signature:**
```python
def run_validation(
    project_id: str,
    mr_iid: str,
    repo_url: str,
    golden_branch: str,
    drift_branch: str,
    target_folder: str = "",
    environment: str = "production"  # ← NEW parameter
) -> dict:
```

### **Step 3.2: Update Instruction String**

**Find the instruction string (around line 1193-1220):**
```python
instruction = f"""
Please orchestrate the complete 2-agent file-based validation workflow:

Project: {project_id}
MR/ID: {mr_iid}
Repository: {repo_url}
Golden Branch: {golden_branch}
Drift Branch: {drift_branch}
Target Folder: {target_folder or "entire repository"}

Complete workflow:
1. Create a unique validation run ID
2. Execute the 2-agent file-based pipeline:
   - Config Collector: Fetch Git diffs, save to drift_analysis file
   - Diff Engine: Read drift_analysis, analyze with AI, save to diff_analysis file
3. Aggregate results from both agents
...
"""
```

**Update to include environment:**
```python
instruction = f"""
Please orchestrate the complete 2-agent file-based validation workflow:

Project: {project_id}
MR/ID: {mr_iid}
Repository: {repo_url}
Golden Branch: {golden_branch}
Drift Branch: {drift_branch}
Target Folder: {target_folder or "entire repository"}
Environment: {environment.upper()}  # ← NEW: Include in instruction

Complete workflow:
1. Create a unique validation run ID
2. Execute the 2-agent file-based pipeline:
   - Config Collector: Fetch Git diffs, save to context_bundle file
   - Diff Engine: Read context_bundle, analyze with AI for {environment} environment, save to llm_output file
3. Aggregate results from both agents
4. Apply {environment}-specific risk assessment rules
...
"""
```

### **Step 3.3: Update execute_worker_pipeline() Signature**

**Find execute_worker_pipeline tool (around line 123):**
```python
@tool
def execute_worker_pipeline(
    project_id: str,
    mr_iid: str,
    run_id: str,
    repo_url: str,
    golden_branch: str,
    drift_branch: str,
    target_folder: str = ""
) -> dict:
```

**Update signature:**
```python
@tool
def execute_worker_pipeline(
    project_id: str,
    mr_iid: str,
    run_id: str,
    repo_url: str,
    golden_branch: str,
    drift_branch: str,
    target_folder: str = "",
    environment: str = "production"  # ← NEW parameter
) -> dict:
```

### **Step 3.4: Pass Environment to Diff Engine**

**Find where Diff Engine task is created (around line 205-230):**
```python
# Step 2: Diff Engine (reads context_bundle, analyzes with policy, saves to enhanced_analysis)
logger.info("Step 2: Running Diff Engine Agent")
diff_engine = DiffPolicyEngineAgent(config)

diff_task = TaskRequest(
    task_id=f"{run_id}_diff",
    task_type="analyze_diffs",
    parameters={
        "context_bundle_file": context_bundle_file
        # ❌ Missing environment
    }
)
```

**Update to:**
```python
# Step 2: Diff Engine (reads context_bundle, analyzes with policy, saves to enhanced_analysis)
logger.info(f"Step 2: Running Diff Engine Agent (environment: {environment})")  # ← NEW: Log
diff_engine = DiffPolicyEngineAgent(config)

diff_task = TaskRequest(
    task_id=f"{run_id}_diff",
    task_type="analyze_diffs",
    parameters={
        "context_bundle_file": context_bundle_file,
        "environment": environment  # ← NEW: Pass environment
    }
)
```

### **✅ Phase 3 Verification:**
```bash
# Check supervisor logs
# Should see: "Step 2: Running Diff Engine Agent (environment: production)"
```

---

## 📋 **PHASE 4: DIFF ENGINE AGENT** (20 minutes)

### **Goal:** Extract environment from task parameters and pass to AI analysis

### **File to Modify:** `strands-multi-agent-system/Agents/workers/diff_policy_engine/diff_engine_agent.py`

### **Step 4.1: Extract Environment in process_task()**

**Find process_task method (around line 81-143):**
```python
def process_task(self, task: TaskRequest) -> TaskResponse:
    start_time = time.time()
    try:
        logger.info("=" * 60)
        logger.info(f"🤖 Diff Engine processing task: {task.task_id}")
        logger.info("=" * 60)
        
        params = task.parameters
        
        # NEW: Support both context_bundle_file (new) and drift_analysis_file (backwards compat)
        context_bundle_file = params.get('context_bundle_file') or params.get('drift_analysis_file')
```

**Add environment extraction after context_bundle_file:**
```python
def process_task(self, task: TaskRequest) -> TaskResponse:
    start_time = time.time()
    try:
        logger.info("=" * 60)
        logger.info(f"🤖 Diff Engine processing task: {task.task_id}")
        logger.info("=" * 60)
        
        params = task.parameters
        
        # NEW: Support both context_bundle_file (new) and drift_analysis_file (backwards compat)
        context_bundle_file = params.get('context_bundle_file') or params.get('drift_analysis_file')
        
        # ← NEW: Extract environment parameter
        environment = params.get('environment', 'production')
        logger.info(f"🌍 Target environment: {environment.upper()}")
```

### **Step 4.2: Pass Environment to Analysis Functions**

**Find where analyze_file_deltas_batch_llm_format is called (around line 180-250):**
```python
# Analyze each file's deltas in batch
for file_path, file_deltas in deltas_by_file.items():
    logger.info(f"  📄 Analyzing {len(file_deltas)} deltas in: {file_path}")
    
    batch_result = await self.analyze_file_deltas_batch_llm_format(
        file=file_path,
        deltas=file_deltas,
        overview=overview
        # ❌ Missing environment
    )
```

**Update to:**
```python
# Analyze each file's deltas in batch
for file_path, file_deltas in deltas_by_file.items():
    logger.info(f"  📄 Analyzing {len(file_deltas)} deltas in: {file_path}")
    
    batch_result = await self.analyze_file_deltas_batch_llm_format(
        file=file_path,
        deltas=file_deltas,
        environment=environment,  # ← NEW: Pass environment
        overview=overview
    )
```

### **Step 4.3: Update Fallback Function**

**Find _fallback_llm_categorization method (around line 1854):**
```python
def _fallback_llm_categorization(self, deltas: list, file: str) -> dict:
    """
    Fallback: Simple rule-based categorization in EXACT LLM format when AI fails.
    ...
    """
    logger.info(f"     🔄 Using fallback rule-based categorization for {len(deltas)} deltas")
```

**Update signature to accept environment:**
```python
def _fallback_llm_categorization(self, deltas: list, file: str, environment: str = "production") -> dict:
    """
    Fallback: Simple rule-based categorization in EXACT LLM format when AI fails.
    NOW WITH ENVIRONMENT AWARENESS!
    ...
    """
    logger.info(f"     🔄 Using fallback rule-based categorization for {len(deltas)} deltas (env: {environment})")
```

### **Step 4.4: Update Fallback Calls**

**Find where fallback is called (search for "_fallback_llm_categorization"):**
```python
logger.warning(f"     ⚠️  AI analysis failed for {file}: {str(e)}")
logger.info("     🔄 Using fallback categorization...")
batch_result = self._fallback_llm_categorization(file_deltas, file_path)
```

**Update to:**
```python
logger.warning(f"     ⚠️  AI analysis failed for {file}: {str(e)}")
logger.info("     🔄 Using fallback categorization...")
batch_result = self._fallback_llm_categorization(file_deltas, file_path, environment)  # ← NEW: Pass environment
```

### **✅ Phase 4 Verification:**
```bash
# Check diff engine logs
# Should see: "🌍 Target environment: PRODUCTION"
# Should see: "🔄 Using fallback... (env: production)"
```

---

## 📋 **PHASE 5: LLM PROMPT ENHANCEMENT** (60 minutes) - **MOST CRITICAL**

### **Goal:** Teach AI to assess risk differently based on environment

### **File to Modify:** `strands-multi-agent-system/Agents/workers/diff_policy_engine/prompts/llm_format_prompt.py`

### **Step 5.1: Add Environment-Specific Guidelines**

**Find the prompt building section (after the deltas summary, around line 77-78):**
```python
    # Add output format specification - EXACT MATCH
    prompt += f"""
## OUTPUT FORMAT
```

**Insert BEFORE "## OUTPUT FORMAT" section:**
```python
    # ← NEW: Add environment-specific risk assessment guidelines
    prompt += f"""
## 🌍 ENVIRONMENT-SPECIFIC RISK ASSESSMENT

You are analyzing for **{environment.upper()}** environment.

### Risk Assessment Rules by Environment:

#### 🔴 PRODUCTION Environment (Current: {'✅ YES' if environment == 'production' else '❌ NO'})
**Strictness Level: MAXIMUM** - Zero tolerance for service disruption

**HIGH Risk (Block deployment):**
- Database connection changes (service will fail to start)
- Security features disabled (compliance violation)
- Production API endpoint changes (integration failures)
- Authentication/authorization modifications (security risk)
- Port changes (service disruption, load balancer issues)
- Feature flags enabled without staging verification

**MEDIUM Risk (Careful review required):**
- Performance settings modified (may degrade under load)
- Timeout/retry configuration changed (may cause failures)
- Logging level to DEBUG (performance impact)
- Network configuration changes (coordination needed)
- Dependency version changes (compatibility risk)

**LOW Risk:**
- Documentation updates
- Comment changes
- Logging level to INFO/WARN

#### 🟡 STAGING Environment (Current: {'✅ YES' if environment == 'staging' else '❌ NO'})
**Strictness Level: MODERATE** - Balance between testing freedom and safety

**HIGH Risk:**
- Security features disabled (even in staging)
- Invalid/malformed configurations (will break testing)

**MEDIUM Risk:**
- Database connection changes (verify staging DB exists)
- Feature flags modified (testing purpose, verify scope)
- Dependency version changes (test compatibility)

**LOW Risk:**
- Port changes (coordination with test team)
- Performance settings (testing flexibility)
- Logging configuration (testing needs)

**ALLOWED:**
- Test data configuration
- Debug settings for troubleshooting

#### 🟡 QA Environment (Current: {'✅ YES' if environment == 'qa' else '❌ NO'})
**Strictness Level: MODERATE** - Similar to staging

**HIGH Risk:**
- Security features disabled
- Invalid configurations

**MEDIUM Risk:**
- Database connection to test DB (verify environment)
- Feature toggles for testing
- Dependency changes (test impact)

**LOW Risk:**
- Network configuration for QA environment
- Performance tuning for tests

**ALLOWED:**
- Test-specific configurations
- Debug/trace logging
- QA-specific feature flags

#### 🟢 DEV Environment (Current: {'✅ YES' if environment == 'dev' else '❌ NO'})
**Strictness Level: MINIMAL** - Development flexibility

**HIGH Risk (still important):**
- Hardcoded credentials in plaintext (security bad practice)
- Known vulnerable dependencies (CVEs)

**MEDIUM Risk:**
- Security features disabled (remind about production)

**LOW Risk:**
- Database connection changes (local development)
- Port changes (local setup)
- Feature experiments

**ALLOWED:**
- Experimental features
- Local database connections
- Debug/trace logging
- Development-specific configurations
- Dependency version experiments

---

## 📝 CATEGORIZATION INSTRUCTIONS FOR {environment.upper()}

Based on the **{environment.upper()}** environment above, adjust your risk assessment:

1. **Check the environment-specific rules** above for this change type
2. **Apply the appropriate risk level** for {environment}
3. **Write environment-specific potential_risk** (what could go wrong in {environment})
4. **Write environment-specific suggested_action** (what to do for {environment})

### Examples for {environment.upper()}:

**Example 1: Database URL Change**
```
Change: datasource.url: prod-db → test-db
"""

    if environment == "production":
        prompt += """
Risk Level: HIGH
potential_risk: "Production database connection changed to test-db! Service will connect to wrong database. Data corruption risk. Production users will see errors."
suggested_action: "URGENT: Revert this change immediately. Verify with DBA team. Production should never connect to test-db. Deploy correct connection string during maintenance window."
```
    elif environment in ["staging", "qa"]:
        prompt += """
Risk Level: MEDIUM
potential_risk: "Test environment database connection changed. Verify test-db is accessible and contains appropriate test data."
suggested_action: "Verify test-db exists and is configured for {environment}. Coordinate with test team. Update test data if needed."
```
    else:  # dev
        prompt += """
Risk Level: ALLOWED
potential_risk: "Dev database connection updated. Normal development activity."
suggested_action: "Document the local database setup in README. Ensure other developers can connect."
```

    prompt += """
```

**Example 2: Feature Flag Toggle**
```
Change: features.newCheckout: false → true
"""

    if environment == "production":
        prompt += """
Risk Level: HIGH
potential_risk: "New checkout feature enabled in production! If not tested in staging, users may experience broken checkout flow. Revenue impact."
suggested_action: "Verify feature was fully tested in staging. Check error rates after deployment. Have rollback plan ready. Monitor checkout completion rates."
```
    elif environment in ["staging", "qa"]:
        prompt += """
Risk Level: LOW
potential_risk: "Feature enabled for testing purposes. Test coverage needed."
suggested_action: "Test the new checkout flow thoroughly. Verify all edge cases. Document test results before promoting to production."
```
    else:  # dev
        prompt += """
Risk Level: ALLOWED
potential_risk: "Feature enabled for development. Normal workflow."
suggested_action: "Continue development. Test locally before pushing to staging."
```

    prompt += """
```

**Example 3: Logging Level Change**
```
Change: logging.level: INFO → DEBUG
"""

    if environment == "production":
        prompt += """
Risk Level: MEDIUM
potential_risk: "DEBUG logging in production will generate excessive logs. Performance degradation likely. Log storage costs will increase. May expose sensitive data in logs."
suggested_action: "Revert to INFO level. Use DEBUG only for temporary troubleshooting. If troubleshooting needed, enable DEBUG for specific package only, not root logger."
```
    else:
        prompt += """
Risk Level: ALLOWED
potential_risk: "DEBUG logging for non-production environment. Normal for troubleshooting."
suggested_action: "Remember to revert to INFO before promoting to production. DEBUG is acceptable for {environment}."
```

    prompt += """
```

---

## ⚠️ CRITICAL REMINDER

**YOU ARE ANALYZING FOR {environment.upper()} ENVIRONMENT**

Apply the **{environment.upper()}-specific** rules above. The same change can have different risk levels in different environments!

"""

    # Now continue with OUTPUT FORMAT section
    prompt += f"""
## OUTPUT FORMAT
```

### **Step 5.2: Update Categorization Examples**

**Find the CATEGORIZATION GUIDELINES section (around line 211-234):**
```python
## CATEGORIZATION GUIDELINES

### **high** (Critical - Database/Security):
- Database credentials changed (usernames, passwords, connection strings)
- Security features disabled
- Production endpoints modified
- Authentication/authorization changes

### **medium** (Important - Configuration/Dependencies):
- Network configuration changes
- Dependency version changes
- Feature behavior modifications
- Performance settings adjusted

### **low** (Minor):
- Logging level changes
- Comment updates
- Minor tweaks

### **allowed_variance** (Acceptable):
- Environment-specific configuration (dev vs qa vs prod differences)
- Test suite configuration
- Build/CI pipeline settings
- Documentation changes
```

**Replace with environment-aware version:**
```python
## CATEGORIZATION GUIDELINES FOR {environment.upper()}

**Remember:** You are analyzing for **{environment.upper()}** environment. Use the environment-specific rules above!

### Quick Reference (adjust based on {environment}):

**high** - Will cause immediate failure or security breach
**medium** - Needs careful review, potential issues
**low** - Minor impact, review recommended
**allowed_variance** - Acceptable for this environment

### Special Cases:

1. **Security Changes:** ALWAYS HIGH in ALL environments
   - Credentials, authentication, encryption

2. **Environment-Specific Configs:** 
   - Database URLs: HIGH in prod, MEDIUM in qa/staging, ALLOWED in dev
   - Feature flags: HIGH in prod (if untested), LOW in qa/staging, ALLOWED in dev
   - Debug logging: MEDIUM in prod, ALLOWED in others
   - Ports: HIGH in prod, MEDIUM in qa/staging, ALLOWED in dev

3. **Documentation:** ALLOWED in all environments
```

### **Step 5.3: Enhance ai_review_assistant Guidelines**

**Find the AI REVIEW ASSISTANT GUIDELINES section (around line 184-200):**
```python
## AI REVIEW ASSISTANT GUIDELINES

The `ai_review_assistant` field is CRITICAL for user decision-making. Be specific and actionable:

### **potential_risk** - Answer "What could go wrong?"
- ✅ GOOD: "Database connection will fail causing 500 errors..."
- ❌ BAD: "Configuration changed" (too generic)
```

**Add environment context:**
```python
## AI REVIEW ASSISTANT GUIDELINES

The `ai_review_assistant` field is CRITICAL for user decision-making.

**IMPORTANT:** Make your assessment **{environment.upper()}-specific**!

### **potential_risk** - Answer "What could go wrong IN {environment.upper()}?"

**For PRODUCTION:**
- ✅ GOOD: "Production database connection will fail causing 500 errors. All users affected. Revenue loss during peak hours."
- ❌ BAD: "Database connection changed" (too generic, not environment-specific)

**For DEV:**
- ✅ GOOD: "Local database connection updated. Other developers may need to update their .env files."
- ❌ BAD: "Service will fail to start" (too alarmist for dev)

**For QA/STAGING:**
- ✅ GOOD: "QA database connection changed. Test suite will fail if QA DB is not ready."
- ❌ BAD: "Users will see errors" (there are no real users in QA)

### **suggested_action** - Answer "What should I do FOR {environment.upper()}?"

**For PRODUCTION:**
- ✅ GOOD: "1. Verify credentials with DBA team. 2. Test connection in staging first. 3. Deploy during maintenance window. 4. Monitor error rates closely."
- ❌ BAD: "Review the change" (not actionable enough for prod)

**For DEV:**
- ✅ GOOD: "Update your local .env file. Run docker-compose up to start local database."
- ❌ BAD: "Test in staging first" (not relevant for dev)

**Remember:** Users need **{environment.upper()}-specific** guidance!
```

---

## 📋 **PHASE 5B: ENHANCE FALLBACK FUNCTION** (30 minutes)

### **Goal:** Make fallback categorization environment-aware

### **File to Modify:** `strands-multi-agent-system/Agents/workers/diff_policy_engine/diff_engine_agent.py`

### **Step 5B.1: Update Fallback Logic**

**Find _fallback_llm_categorization method (around line 1854-1977):**

**Current logic (simplified):**
```python
def _fallback_llm_categorization(self, deltas: list, file: str, environment: str = "production") -> dict:
    result = {"high": [], "medium": [], "low": [], "allowed_variance": []}
    
    for delta in deltas:
        policy_tag = delta.get('policy', {}).get('tag', '').lower()
        old_val = str(delta.get('old', '')).lower()
        new_val = str(delta.get('new', '')).lower()
        
        # Determine bucket using simple rules
        if any(keyword in old_val or keyword in new_val for keyword in ['password', 'secret', 'key']):
            bucket = 'high'
        elif any(keyword in old_val or keyword in new_val for keyword in ['port', 'host', 'url']):
            bucket = 'medium'
        else:
            bucket = 'low'
```

**Update with environment awareness:**
```python
def _fallback_llm_categorization(self, deltas: list, file: str, environment: str = "production") -> dict:
    """
    Fallback: Rule-based categorization with ENVIRONMENT AWARENESS
    """
    logger.info(f"     🔄 Using environment-aware fallback for {len(deltas)} deltas (env: {environment})")
    
    result = {"high": [], "medium": [], "low": [], "allowed_variance": []}
    
    for delta in deltas:
        policy_tag = delta.get('policy', {}).get('tag', '').lower()
        old_val = str(delta.get('old', '')).lower()
        new_val = str(delta.get('new', '')).lower()
        category = delta.get('category', 'unknown')
        
        # === ENVIRONMENT-AWARE CATEGORIZATION ===
        
        # 1. Security: ALWAYS HIGH (all environments)
        if any(keyword in old_val or keyword in new_val for keyword in ['password', 'secret', 'key', 'token', 'credential']):
            bucket = 'high'
            risk = "Security credential changed. Authentication failures will occur in {}.".format(environment)
            action = "Verify credentials with security team. Test authentication. Deploy during maintenance window." if environment == 'production' else "Update credentials in {} environment configuration.".format(environment)
        
        # 2. Database connections: Environment-dependent
        elif any(keyword in old_val or keyword in new_val for keyword in ['jdbc', 'datasource', 'database', 'db.url']):
            if environment == 'production':
                bucket = 'high'
                risk = "Production database connection changed. Service will fail to start. All users affected."
                action = "URGENT: Verify with DBA team. Test connection immediately. Monitor service health."
            elif environment in ['staging', 'qa']:
                bucket = 'medium'
                risk = "{} database connection changed. Test environment may fail to start.".format(environment.upper())
                action = "Verify {} database is accessible. Update test data if needed.".format(environment)
            else:  # dev
                bucket = 'allowed_variance'
                risk = "Dev database connection updated for local development."
                action = "Update your local .env file. Document connection details in README."
        
        # 3. Port changes: Environment-dependent
        elif 'port' in old_val or 'server.port' in old_val:
            if environment == 'production':
                bucket = 'high'
                risk = "Production port changed. Service disruption. Load balancer misconfiguration. Users cannot connect."
                action = "Verify port with infrastructure team. Update load balancer. Test connectivity. Deploy during maintenance."
            elif environment in ['staging', 'qa']:
                bucket = 'medium'
                risk = "{} port changed. Coordination with test team needed.".format(environment.upper())
                action = "Notify test team. Update test configurations. Verify firewall rules."
            else:  # dev
                bucket = 'allowed_variance'
                risk = "Dev port changed for local setup."
                action = "Update your local configuration. Document in README."
        
        # 4. URL/Endpoint changes: Environment-dependent
        elif any(keyword in old_val or keyword in new_val for keyword in ['url', 'endpoint', 'host', 'http']):
            if environment == 'production':
                bucket = 'high'
                risk = "Production endpoint changed. API calls will fail. Integration broken. Service unavailable."
                action = "Verify with service owner. Test connectivity. Check firewall rules. Update DNS. Monitor integration health."
            elif environment in ['staging', 'qa']:
                bucket = 'medium'
                risk = "{} endpoint changed. Test integrations may fail.".format(environment.upper())
                action = "Verify {} endpoint is accessible. Update test configurations.".format(environment)
            else:  # dev
                bucket = 'low'
                risk = "Dev endpoint changed for local development."
                action = "Update local configuration. Test connectivity."
        
        # 5. Feature flags: Environment-dependent
        elif any(keyword in old_val for keyword in ['feature', 'flag', 'enabled', 'disabled']):
            if environment == 'production':
                bucket = 'medium'
                risk = "Feature behavior changed in production. User experience impact. Potential bugs if not tested."
                action = "Verify feature was tested in staging. Monitor error rates. Have rollback plan ready."
            elif environment in ['staging', 'qa']:
                bucket = 'low'
                risk = "Feature toggle for testing in {}.".format(environment)
                action = "Test thoroughly. Verify all scenarios. Document results."
            else:  # dev
                bucket = 'allowed_variance'
                risk = "Feature toggle for development."
                action = "Continue development. Test locally."
        
        # 6. Logging level: Environment-dependent
        elif 'logging' in old_val or 'log.level' in old_val:
            if 'debug' in new_val or 'trace' in new_val:
                if environment == 'production':
                    bucket = 'medium'
                    risk = "DEBUG logging in production will impact performance. Excessive log volume. May expose sensitive data."
                    action = "Revert to INFO. Use DEBUG only for troubleshooting specific packages, not root logger."
                else:
                    bucket = 'allowed_variance'
                    risk = "DEBUG logging for {} environment.".format(environment)
                    action = "Normal for troubleshooting. Remember to revert before production."
            else:
                bucket = 'low'
                risk = "Logging configuration changed."
                action = "Review log levels for appropriateness."
        
        # 7. Dependencies: Environment-dependent severity
        elif category.startswith('dependency'):
            if environment == 'production':
                bucket = 'medium'
                risk = "Dependency modified in production. Breaking API changes possible. Security vulnerabilities. Compatibility issues."
                action = "Review changelog. Run full test suite. Check for CVEs. Verify compatibility. Test in staging first."
            elif environment in ['staging', 'qa']:
                bucket = 'medium'
                risk = "Dependency modified. Test impact on {} environment.".format(environment)
                action = "Run test suite. Verify no breaking changes. Check compatibility."
            else:  # dev
                bucket = 'low'
                risk = "Dependency modified for development."
                action = "Test locally. Update documentation if needed."
        
        # 8. Default: Environment-dependent
        else:
            if environment == 'production':
                bucket = 'medium'
                risk = "Production configuration changed. Potential impact unknown."
                action = "Review change carefully. Test in staging. Monitor after deployment."
            elif environment in ['staging', 'qa']:
                bucket = 'low'
                risk = "{} configuration changed.".format(environment.upper())
                action = "Review and test the change."
            else:  # dev
                bucket = 'allowed_variance'
                risk = "Dev configuration changed."
                action = "Normal development activity."
        
        # Build item structure
        item = {
            "id": delta.get('id'),
            "file": file,
            "locator": delta.get('locator', {})
        }
        
        # Add old/new values
        item["old"] = str(delta.get('old', '')) if delta.get('old') is not None else None
        item["new"] = str(delta.get('new', '')) if delta.get('new') is not None else None
        
        # Add drift_category
        if 'password' in old_val or 'secret' in old_val or 'credential' in old_val:
            drift_cat = "Database"
        elif 'jdbc' in old_val or 'datasource' in old_val or 'database' in old_val:
            drift_cat = "Database"
        elif 'url' in old_val or 'endpoint' in old_val or 'host' in old_val or 'port' in old_val:
            drift_cat = "Network"
        elif category.startswith('dependency'):
            drift_cat = "Dependency"
        elif 'feature' in old_val or 'flag' in old_val or 'enabled' in old_val:
            drift_cat = "Functional"
        elif 'timeout' in old_val or 'cache' in old_val or 'pool' in old_val:
            drift_cat = "Configuration"
        else:
            drift_cat = "Configuration"
        
        item["drift_category"] = drift_cat
        
        if bucket == 'allowed_variance':
            item["rationale"] = risk
        else:
            item["why"] = risk
            item["ai_review_assistant"] = {
                "potential_risk": risk,
                "suggested_action": action
            }
            item["remediation"] = {
                "snippet": str(delta.get('old', ''))
            }
        
        result[bucket].append(item)
    
    logger.info(f"     ✅ Environment-aware fallback ({environment}): High={len(result['high'])}, "
               f"Medium={len(result['medium'])}, Low={len(result['low'])}, Allowed={len(result['allowed_variance'])}")
    
    return result
```

---

## 📋 **TESTING PLAN**

### **Test 1: Production Service**
```bash
# Analyze cxp_ordering_services (production)
curl -X POST http://localhost:3000/api/services/cxp_ordering_services/analyze

# Expected:
# - Environment: PRODUCTION logged
# - Stricter risk assessment
# - Database changes = HIGH
# - Feature flags = MEDIUM-HIGH
```

### **Test 2: Dev Service**
```bash
# Analyze cxp_config_properties (dev)
curl -X POST http://localhost:3000/api/services/cxp_config_properties/analyze

# Expected:
# - Environment: DEV logged
# - Lenient risk assessment
# - Database changes = ALLOWED
# - Feature experiments = ALLOWED
```

### **Test 3: QA Service**
```bash
# Analyze cxp_credit_services (qa)
curl -X POST http://localhost:3000/api/services/cxp_credit_services/analyze

# Expected:
# - Environment: QA logged
# - Moderate risk assessment
# - Database changes = MEDIUM
# - Feature toggles = LOW
```

---

## 🎯 **IMPLEMENTATION ORDER**

### **Day 1: Foundation (Phases 1-3, 1 hour)**
1. ✅ Phase 1: Add environment to SERVICES_CONFIG (15 min)
2. ✅ Phase 2: Update API endpoints (20 min)
3. ✅ Phase 3: Update supervisor agent (15 min)
4. ✅ Test: Environment flows through pipeline (10 min)

### **Day 2: AI Integration (Phases 4-5, 2 hours)**
1. ✅ Phase 4: Update diff engine agent (20 min)
2. ✅ Phase 5: Enhance LLM prompt (60 min)
3. ✅ Phase 5B: Enhance fallback (30 min)
4. ✅ Test: Full end-to-end with all three services (10 min)

---

## ✅ **VERIFICATION CHECKLIST**

After implementation, verify:

- [ ] All 3 services have environment field in SERVICES_CONFIG
- [ ] API logs show: "🌍 Analyzing {service} for environment: {ENV}"
- [ ] Supervisor logs show: "Environment: {ENV}"
- [ ] Diff engine logs show: "🌍 Target environment: {ENV}"
- [ ] LLM prompt includes environment-specific guidelines
- [ ] Fallback function is environment-aware
- [ ] Production service gets stricter risk assessment
- [ ] Dev service gets lenient risk assessment
- [ ] Same drift has different risk levels in prod vs. dev
- [ ] AI recommendations are environment-specific

---

## 🚀 **READY TO IMPLEMENT?**

This plan is ready for execution. Each phase builds on the previous one, and the changes are backward compatible (defaults to "production" if environment not specified).

**Estimated time:** 2-3 hours total
**Risk:** Low (backward compatible)
**Impact:** High (environment-aware analysis)

Let me know when you're ready to start, and I'll implement phase by phase! 🎯

