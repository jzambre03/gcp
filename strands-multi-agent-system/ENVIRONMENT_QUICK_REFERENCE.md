# 🎯 Environment-Aware Analysis - Quick Reference

## 📊 **CURRENT vs. FUTURE BEHAVIOR**

### **BEFORE (Current System):**
```
Change: datasource.url: prod-db → test-db

Service: cxp_ordering_services    → Risk: HIGH ⚠️
Service: cxp_credit_services      → Risk: HIGH ⚠️
Service: cxp_config_properties    → Risk: HIGH ⚠️

Problem: Same risk for all services, regardless of environment!
```

### **AFTER (Environment-Aware System):**
```
Change: datasource.url: prod-db → test-db

Service: cxp_ordering_services (production)  → Risk: HIGH ⚠️
  "Production database changed! Service will fail. Urgent review."

Service: cxp_credit_services (qa)            → Risk: MEDIUM ⚠️
  "QA database changed. Verify test environment is ready."

Service: cxp_config_properties (dev)         → Risk: ALLOWED ✅
  "Dev database updated. Normal development activity."

Solution: Risk adjusts based on target environment!
```

---

## 🚀 **IMPLEMENTATION: 5 PHASES**

```
Phase 1: SERVICES_CONFIG       [15 min]  ← Add environment field
    ↓
Phase 2: API Endpoints         [20 min]  ← Pass environment to validation
    ↓
Phase 3: Supervisor Agent      [15 min]  ← Forward environment through pipeline
    ↓
Phase 4: Diff Engine Agent     [20 min]  ← Extract & pass to AI
    ↓
Phase 5: LLM Prompt            [60 min]  ← Environment-specific guidelines (CRITICAL!)
    ↓
Phase 5B: Fallback Function    [30 min]  ← Environment-aware rules

TOTAL: 2.5 hours
```

---

## 📋 **WHAT CHANGES IN EACH FILE**

### **1. main.py** (Phases 1-2)
```python
# BEFORE:
SERVICES_CONFIG = {
    "cxp_ordering_services": {
        "name": "CXP Ordering Services",
        "repo_url": "...",
        "golden_branch": "golden",
        "drift_branch": "drifted"
    }
}

# AFTER:
SERVICES_CONFIG = {
    "cxp_ordering_services": {
        "name": "CXP Ordering Services",
        "repo_url": "...",
        "golden_branch": "golden",
        "drift_branch": "drifted",
        "environment": "production"  # ← NEW!
    }
}

# AND:
result = run_validation(
    ...,
    environment=config["environment"]  # ← NEW!
)
```

### **2. supervisor_agent.py** (Phase 3)
```python
# BEFORE:
def run_validation(..., target_folder: str = "") -> dict:

# AFTER:
def run_validation(..., target_folder: str = "", environment: str = "production") -> dict:

# AND:
diff_task = TaskRequest(
    parameters={
        "context_bundle_file": ...,
        "environment": environment  # ← NEW!
    }
)
```

### **3. diff_engine_agent.py** (Phase 4)
```python
# BEFORE:
params = task.parameters
context_bundle_file = params.get('context_bundle_file')

# AFTER:
params = task.parameters
context_bundle_file = params.get('context_bundle_file')
environment = params.get('environment', 'production')  # ← NEW!

# AND:
batch_result = await self.analyze_file_deltas_batch_llm_format(
    file=file_path,
    deltas=file_deltas,
    environment=environment,  # ← NEW!
    overview=overview
)
```

### **4. llm_format_prompt.py** (Phase 5 - MOST IMPORTANT)
```python
# BEFORE:
prompt = f"""You are analyzing file "{file}" for environment "{environment}".

Your task is to categorize changes...
"""

# AFTER:
prompt = f"""You are analyzing file "{file}" for environment "{environment}".

## 🌍 ENVIRONMENT-SPECIFIC RISK ASSESSMENT

You are analyzing for **{environment.upper()}** environment.

#### 🔴 PRODUCTION (Strictness: MAXIMUM)
- Database changes: HIGH (service failure)
- Port changes: HIGH (disruption)
- Feature flags: HIGH if untested

#### 🟡 QA/STAGING (Strictness: MODERATE)
- Database changes: MEDIUM (coordination)
- Feature flags: LOW (testing purpose)

#### 🟢 DEV (Strictness: MINIMAL)
- Database changes: ALLOWED (local dev)
- Feature flags: ALLOWED (experiments)

Apply {environment.upper()}-specific rules...
"""
```

### **5. diff_engine_agent.py - Fallback** (Phase 5B)
```python
# BEFORE:
def _fallback_llm_categorization(self, deltas, file):
    if 'database' in value:
        bucket = 'high'  # Always high!

# AFTER:
def _fallback_llm_categorization(self, deltas, file, environment="production"):
    if 'database' in value:
        if environment == 'production':
            bucket = 'high'
        elif environment in ['qa', 'staging']:
            bucket = 'medium'
        else:  # dev
            bucket = 'allowed_variance'
```

---

## 🎯 **RISK ASSESSMENT MATRIX**

| Change Type | Production | QA/Staging | Dev |
|-------------|-----------|-----------|-----|
| **Database Connection** | 🔴 HIGH | 🟡 MEDIUM | 🟢 ALLOWED |
| **Security Credentials** | 🔴 HIGH | 🔴 HIGH | 🔴 HIGH |
| **Port Change** | 🔴 HIGH | 🟡 MEDIUM | 🟢 ALLOWED |
| **Feature Flag** | 🔴 HIGH (untested) | 🟡 LOW | 🟢 ALLOWED |
| **Debug Logging** | 🟡 MEDIUM | 🟢 ALLOWED | 🟢 ALLOWED |
| **Dependency Update** | 🟡 MEDIUM | 🟡 MEDIUM | 🟡 LOW |
| **Documentation** | 🟢 ALLOWED | 🟢 ALLOWED | 🟢 ALLOWED |

---

## ✅ **TESTING SCENARIOS**

### **Scenario 1: Database URL Change**
```bash
# Drift: datasource.url: prod-db → test-db

# Test 1: Production Service
curl -X POST http://localhost:3000/api/services/cxp_ordering_services/analyze
Expected: HIGH risk, "Production database changed! Service will fail."

# Test 2: Dev Service  
curl -X POST http://localhost:3000/api/services/cxp_config_properties/analyze
Expected: ALLOWED, "Dev database updated. Normal development."
```

### **Scenario 2: Feature Flag Toggle**
```bash
# Drift: features.newUI: false → true

# Test 1: Production Service
Expected: HIGH/MEDIUM risk, "Verify tested in staging first."

# Test 2: QA Service
Expected: LOW risk, "Testing purpose. Test thoroughly."

# Test 3: Dev Service
Expected: ALLOWED, "Development experiment."
```

---

## 🔍 **HOW TO VERIFY IT'S WORKING**

### **Check 1: Logs**
```bash
# Start the server
cd strands-multi-agent-system
python3 main.py

# Trigger analysis
curl -X POST http://localhost:3000/api/services/cxp_ordering_services/analyze

# Look for these logs:
✅ "🌍 Analyzing cxp_ordering_services for environment: PRODUCTION"
✅ "🌍 Target environment: PRODUCTION"
✅ "Environment-aware fallback (env: production)"
```

### **Check 2: LLM Output**
```bash
# Check the generated llm_output.json
cat config_data/llm_output/llm_output_*.json | jq '.high[0].ai_review_assistant'

# Should see environment-specific risk:
{
  "potential_risk": "Production database changed! Service will fail...",
  "suggested_action": "URGENT: Verify with DBA. Test immediately..."
}

# NOT generic:
{
  "potential_risk": "Database changed",  ← BAD
  "suggested_action": "Review the change"  ← BAD
}
```

### **Check 3: Compare Environments**
```bash
# Analyze all 3 services (different environments)
curl -X POST http://localhost:3000/api/services/cxp_ordering_services/analyze
curl -X POST http://localhost:3000/api/services/cxp_credit_services/analyze
curl -X POST http://localhost:3000/api/services/cxp_config_properties/analyze

# Compare results - same drift should have:
# - Different risk levels
# - Different recommendations
# - Environment-specific language
```

---

## 🚀 **QUICK START GUIDE**

### **Step 1: Configure Environments** (5 min)
Edit `main.py`, add environment to each service:
```python
"environment": "production"  # or "qa", "staging", "dev"
```

### **Step 2: Update Validation Chain** (30 min)
Follow phases 2-4 in the implementation plan.

### **Step 3: Enhance AI Prompt** (60 min)
Add environment-specific guidelines to `llm_format_prompt.py`.

### **Step 4: Test** (15 min)
Run analysis on all 3 services, verify environment-specific results.

---

## 📊 **EXPECTED RESULTS**

### **Before Implementation:**
```
All Services → Same risk assessment → Generic recommendations
```

### **After Implementation:**
```
Production   → Strict assessment    → Urgent, specific actions
QA/Staging   → Moderate assessment  → Test-focused actions
Dev          → Lenient assessment   → Development-friendly guidance
```

---

## 💡 **KEY BENEFITS**

✅ **Noise Reduction:** Dev changes won't trigger false alarms
✅ **Production Safety:** Production gets extra scrutiny
✅ **Context-Aware:** Same change = different risk based on target
✅ **Actionable:** Environment-specific recommendations
✅ **Realistic:** Matches real-world deployment patterns

---

## 📝 **NEXT STEPS**

1. Review the full plan: `ENVIRONMENT_IMPLEMENTATION_PLAN.md`
2. Decide on environment labels for your 3 services
3. Start with Phase 1 (15 minutes)
4. Progress through phases 2-5
5. Test with real drifts

**Ready to implement? Let's start with Phase 1!** 🎯

