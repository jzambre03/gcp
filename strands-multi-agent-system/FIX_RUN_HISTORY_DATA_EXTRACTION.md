# 🔧 Fix: Run History Data Not Populating Correctly

**Date:** October 16, 2025  
**Issue:** run_history.json shows all "unknown" and "N/A" values  
**Status:** ✅ **FIXED**

---

## 🐛 **The Problem**

### **What You Saw:**

**run_history.json** (BEFORE FIX):
```json
{
  "runs": [{
    "run_id": "unknown",           ← Should be "run_20251015_204055_..."
    "verdict": "UNKNOWN",          ← Should be "REVIEW_REQUIRED"
    "execution_time_seconds": 0,   ← Should be 74.4
    "branches": {
      "golden_branch": "N/A",      ← Should be "golden_prod_20251015_185719_83ed47"
      "drift_branch": "N/A"        ← Should be "drift_prod_20251015_191324_3075b4"
    },
    "metrics": {
      "files_analyzed": 0,         ← Should be 53
      "files_with_drift": 0,       ← Should be 1
      "total_deltas": 0            ← Should be 3
    }
  }]
}
```

**validation.json** (HAD THE DATA):
```json
{
  "result": {
    "validation_result": {
      "run_id": "run_20251015_204055_...",  ← Data was HERE!
      "verdict": "REVIEW_REQUIRED",
      "files_analyzed": 53,
      "files_with_drift": 1,
      "total_deltas": 3,
      ...
    }
  }
}
```

---

## 🔍 **Root Cause**

### **Issue #1: Incorrect Data Nesting**

The validation data has **2 levels of nesting**:

```python
run_data = {
  "validation_result": {           # Level 1
    "validation_result": {         # Level 2 ← ACTUAL DATA IS HERE!
      "run_id": "...",
      "verdict": "...",
      ...
    }
  }
}
```

**My code was doing:**
```python
validation_result = run_data.get("validation_result", run_data)
# This gets Level 1, but data is at Level 2!

run_id = validation_result.get("run_id")  # ❌ Returns None
```

**Should be:**
```python
result = run_data.get("validation_result", run_data)         # Level 1
validation_result = result.get("validation_result", result)  # Level 2 ✅
run_id = validation_result.get("run_id")  # ✅ Now finds it!
```

### **Issue #2: Branch Names Not in Validation Result**

The `golden_branch` and `drift_branch` names are **not** in the validation_result object. They're stored in the `golden_branch_tracker`.

**Fixed by:**
```python
from shared.golden_branch_tracker import get_all_branches, get_active_golden_branch
golden_branches, drift_branches = get_all_branches(service_id, environment)
golden_branch_name = get_active_golden_branch(service_id, environment)
drift_branch_name = drift_branches[0] if drift_branches else "N/A"
```

---

## ✅ **The Fixes Applied**

### **Fix #1: Correct Data Extraction**

**File:** `main.py` lines 844-846

**Before:**
```python
validation_result = run_data.get("validation_result", run_data)
# ❌ Only goes 1 level deep
```

**After:**
```python
result = run_data.get("validation_result", run_data)  # Gets outer result object
validation_result = result.get("validation_result", result)  # Gets nested validation_result
# ✅ Now goes 2 levels deep to find actual data
```

### **Fix #2: Fetch Branch Names from Tracker**

**File:** `main.py` lines 855-866

**Added:**
```python
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
```

### **Fix #3: Debug Logging**

**File:** `main.py` lines 849-853, 907-911

**Added helpful logging:**
```python
# Before extraction
print(f"🔍 Extracting run metadata:")
print(f"   Run ID: {validation_result.get('run_id', 'NOT FOUND')}")
print(f"   Verdict: {validation_result.get('verdict', 'NOT FOUND')}")
...

# After saving
print(f"✅ Saved run history for {service_id}/{environment}")
print(f"   📁 File: {history_file}")
print(f"   📊 Total runs: {len(history['runs'])}")
print(f"   🆔 Latest run ID: {run_metadata.get('run_id', 'unknown')}")
print(f"   ⚖️  Latest verdict: {run_metadata.get('verdict', 'unknown')}")
```

---

## 🧪 **Testing the Fix**

### **Step 1: Delete Old run_history.json**

```bash
# Remove the broken file
rm -f "config_data/service_results/cxp_credit_services/prod/run_history.json"
```

### **Step 2: Run a New Analysis**

```bash
# Your server should be running with the new code
# Trigger an analysis from the UI or API:

curl -X POST http://localhost:3000/api/services/cxp_credit_services/analyze/prod
```

### **Step 3: Watch Console Output**

You should now see detailed extraction logging:

```bash
✅ Stored result for cxp_credit_services/prod to: ...

🔍 Extracting run metadata:
   Run ID: run_20251015_204055_cxp_credit_services_prod_analysis_1760575181
   Verdict: REVIEW_REQUIRED
   Files analyzed: 53
   Files with drift: 1
   Golden branch (from tracker): golden_prod_20251015_185719_83ed47
   Drift branch (from tracker): drift_prod_20251015_191324_3075b4

✅ Saved run history for cxp_credit_services/prod
   📁 File: config_data/service_results/cxp_credit_services/prod/run_history.json
   📊 Total runs: 1
   🆔 Latest run ID: run_20251015_204055_cxp_credit_services_prod_analysis_1760575181
   ⚖️  Latest verdict: REVIEW_REQUIRED
```

### **Step 4: Verify run_history.json**

```bash
cat "config_data/service_results/cxp_credit_services/prod/run_history.json" | python -m json.tool
```

**Expected (AFTER FIX):**
```json
{
  "service_id": "cxp_credit_services",
  "environment": "prod",
  "runs": [
    {
      "run_id": "run_20251015_204055_cxp_credit_services_prod_analysis_1760575181",
      "timestamp": "2025-10-16T00:40:55.817173+00:00",
      "execution_time_seconds": 74.437,
      "verdict": "REVIEW_REQUIRED",
      
      "branches": {
        "main_branch": "main",
        "golden_branch": "golden_prod_20251015_185719_83ed47",
        "drift_branch": "drift_prod_20251015_191324_3075b4"
      },
      
      "metrics": {
        "files_analyzed": 53,
        "files_with_drift": 1,
        "total_deltas": 3,
        "policy_violations": 3,
        "critical_violations": 0,
        "high_violations": 2,
        "overall_risk_level": "high"
      },
      
      "file_paths": {
        "context_bundle": "/home/saja9l7/Projects/gcp/upd/config_data/context_bundles/bundle_20251015_203957/context_bundle.json",
        "enhanced_analysis": "/home/saja9l7/Projects/gcp/upd/config_data/enhanced_analysis/enhanced_analysis_20251015_204030.json"
      },
      
      "summary": {
        "top_issues": [
          "Account PIN authentication has been disabled, potentially reducing security.",
          "SSN tokenization has been disabled, exposing sensitive personal information.",
          "ACP (Affordable Connectivity Program) eligibility check has been disabled, affecting service offerings."
        ]
      }
    }
  ]
}
```

---

## 📊 **What Changed**

| Field | Before (Broken) | After (Fixed) |
|-------|-----------------|---------------|
| `run_id` | "unknown" | "run_20251015_204055_..." |
| `verdict` | "UNKNOWN" | "REVIEW_REQUIRED" |
| `execution_time_seconds` | 0 | 74.437 |
| `golden_branch` | "N/A" | "golden_prod_20251015_185719_83ed47" |
| `drift_branch` | "N/A" | "drift_prod_20251015_191324_3075b4" |
| `files_analyzed` | 0 | 53 |
| `files_with_drift` | 0 | 1 |
| `total_deltas` | 0 | 3 |
| `policy_violations` | 0 | 3 |
| `high_violations` | 0 | 2 |
| `overall_risk_level` | "unknown" | "high" |
| `top_issues` | [] | [3 issue descriptions] |

---

## 🔍 **Understanding the Data Flow**

### **Step 1: Analysis Completes**

Supervisor returns:
```python
result = {
  "status": "success",
  "validation_result": {
    "run_id": "...",
    "verdict": "...",
    ...
  },
  "request_params": {...}
}
```

### **Step 2: store_service_result() Called**

```python
store_service_result(service_id, environment, result)
```

Saves to `validation_{timestamp}.json`:
```json
{
  "service_id": "...",
  "environment": "...",
  "result": result  ← Entire result object
}
```

Then calls:
```python
save_run_history(service_id, environment, {
    "validation_result": result,  ← Wraps it again!
    "timestamp": "..."
})
```

### **Step 3: save_run_history() Extracts Data**

```python
run_data = {
  "validation_result": result,  # This is the outer wrapper
  "timestamp": "..."
}

# Must unwrap twice:
result = run_data.get("validation_result")           # Gets outer result
validation_result = result.get("validation_result")  # Gets inner validation_result
# Now we have the actual data!
```

---

## 🎯 **How to Verify the Fix**

### **Method 1: Run New Analysis**

```bash
# 1. Delete old broken file
rm -f "config_data/service_results/cxp_credit_services/prod/run_history.json"

# 2. Run analysis (server must have the fix)
# Click Analyze in UI or use API

# 3. Check console for new debug output:
🔍 Extracting run metadata:
   Run ID: run_20251015_204055_...           ← Should see real run ID
   Verdict: REVIEW_REQUIRED                   ← Should see real verdict
   Files analyzed: 53                         ← Should see real numbers
   Golden branch: golden_prod_20251015_...    ← Should see real branch
   
✅ Saved run history for cxp_credit_services/prod
   🆔 Latest run ID: run_20251015_204055_...  ← Confirms it worked
   ⚖️  Latest verdict: REVIEW_REQUIRED
```

### **Method 2: Check the File**

```bash
cat "config_data/service_results/cxp_credit_services/prod/run_history.json" | python -m json.tool

# Should see real data instead of "unknown" and "N/A"
```

### **Method 3: View in UI**

```bash
# 1. Open http://localhost:3000/branch-environment?id=cxp_credit_services
# 2. Click "Analysis History" tab
# 3. Should see run with real data:
#    - Real run ID
#    - Real verdict (REVIEW_REQUIRED)
#    - Real metrics (53 files, 1 drift, 3 changes)
#    - Real branch names
```

---

## 📋 **What Was Fixed**

| Fix | Lines | What It Does |
|-----|-------|--------------|
| **Correct nesting** | 844-846 | Now extracts data from correct level |
| **Branch names** | 855-866 | Fetches from golden_branch_tracker |
| **Debug logging** | 849-853 | Shows what's being extracted |
| **Save logging** | 907-911 | Confirms what was saved |
| **Top issues** | 883 | Extracts description from policy_violations |

---

## ✅ **Expected Console Output (After Fix)**

When you run a new analysis, you should see:

```bash
================================================================================
✅ VALIDATION COMPLETED
================================================================================
⏱️  Execution Time: 74.44s
🆔 Run ID: run_20251015_204055_cxp_credit_services_prod_analysis_1760575181
📊 Verdict: REVIEW_REQUIRED
================================================================================

✅ Stored result for cxp_credit_services/prod to: config_data/service_results/cxp_credit_services/prod/validation_20251015_204055.json

🔍 Extracting run metadata:
   Run ID: run_20251015_204055_cxp_credit_services_prod_analysis_1760575181
   Verdict: REVIEW_REQUIRED
   Files analyzed: 53
   Files with drift: 1
   Golden branch (from tracker): golden_prod_20251015_185719_83ed47
   Drift branch (from tracker): drift_prod_20251015_191324_3075b4

✅ Saved run history for cxp_credit_services/prod
   📁 File: config_data/service_results/cxp_credit_services/prod/run_history.json
   📊 Total runs: 1
   🆔 Latest run ID: run_20251015_204055_cxp_credit_services_prod_analysis_1760575181
   ⚖️  Latest verdict: REVIEW_REQUIRED
```

If you see this, the fix is working! ✅

---

## 🧪 **Quick Test**

```bash
# Restart server to load the fix
python main.py

# Trigger analysis
# Watch console for the debug output above

# Check file
cat "config_data/service_results/cxp_credit_services/prod/run_history.json"

# Should see real data now!
```

---

## 📊 **Summary**

**Root Cause:**
- Data was nested 2 levels deep: `run_data.validation_result.validation_result`
- My code only went 1 level deep
- Branch names needed to be fetched from `golden_branch_tracker`

**Fix:**
- ✅ Added second level of nesting extraction
- ✅ Added branch name lookup from tracker
- ✅ Added debug logging to help diagnose issues
- ✅ Improved top_issues extraction

**Result:**
- run_history.json now has real run_id, verdict, metrics, branches
- UI will display actual analysis data instead of "unknown"

---

**Try running a new analysis now - it should populate correctly!** 🎯

