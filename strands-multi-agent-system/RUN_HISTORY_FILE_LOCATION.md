# 📁 Run History File - Location & Structure

**Question:** Are we creating a new JSON file? Where and what name?  
**Answer:** ✅ **YES - One `run_history.json` file per service/environment**

---

## 📂 **File Location**

### **File Name:**
```
run_history.json
```

### **File Path:**
```
config_data/service_results/{service_id}/{environment}/run_history.json
```

### **Real Examples:**

```
config_data/
└── service_results/
    ├── cxp_credit_services/
    │   ├── prod/
    │   │   ├── run_history.json          ← History for CXP Credit Services / Production
    │   │   ├── validation_20251015_191319.json
    │   │   ├── validation_20251015_185827.json
    │   │   └── validation_20251015_141810.json
    │   ├── dev/
    │   │   └── run_history.json          ← History for CXP Credit Services / Development
    │   ├── qa/
    │   │   └── run_history.json          ← History for CXP Credit Services / QA
    │   └── staging/
    │       └── run_history.json          ← History for CXP Credit Services / Staging
    │
    ├── cxp_ordering_services/
    │   ├── prod/
    │   │   └── run_history.json          ← History for CXP Ordering Services / Production
    │   ├── dev/
    │   │   └── run_history.json
    │   ├── qa/
    │   │   └── run_history.json
    │   └── staging/
    │       └── run_history.json
    │
    └── cxp_config_properties/
        ├── prod/
        │   └── run_history.json          ← History for CXP Config Properties / Production
        ├── dev/
        │   └── run_history.json
        ├── qa/
        │   └── run_history.json
        └── staging/
            └── run_history.json
```

---

## 📊 **Key Points**

### **1. One File Per Service/Environment Combination**

```
Service: cxp_credit_services
Environments: [prod, dev, qa, staging]

Creates 4 files:
  ├─ config_data/service_results/cxp_credit_services/prod/run_history.json
  ├─ config_data/service_results/cxp_credit_services/dev/run_history.json
  ├─ config_data/service_results/cxp_credit_services/qa/run_history.json
  └─ config_data/service_results/cxp_credit_services/staging/run_history.json
```

### **2. Each File Stores All Runs for That Combination**

```json
// cxp_credit_services/prod/run_history.json
{
  "service_id": "cxp_credit_services",
  "environment": "prod",
  "runs": [
    { "run_id": "run_20251015_191319_...", ... },  ← Most recent
    { "run_id": "run_20251015_185827_...", ... },
    { "run_id": "run_20251015_141810_...", ... }   ← Oldest
  ]
}
```

### **3. Maximum 50 Runs Kept**

The file automatically keeps only the **last 50 runs** to prevent it from growing too large.

Older runs are automatically removed when the limit is reached.

---

## 🔍 **File Creation Code**

### **Where It's Created:**

```python
# main.py line 830
history_file = Path("config_data") / "service_results" / service_id / environment / "run_history.json"
```

### **When It's Created:**

**Automatically created after every analysis!**

```python
# main.py line 797-800
# In store_service_result() function:

# NEW: Save to run history for UI display
save_run_history(service_id, environment, {
    "validation_result": result,
    "timestamp": datetime.now(timezone.utc).isoformat()
})
```

**Triggered by:**
- User clicks "Analyze" button
- Analysis completes
- `store_service_result()` is called
- `save_run_history()` is called automatically
- File is created/updated

---

## 📋 **Complete File Structure Example**

After running analyses for **cxp_credit_services** in **prod** 3 times:

```
config_data/
├── service_results/
│   └── cxp_credit_services/
│       └── prod/
│           ├── run_history.json               ← NEW! Stores all 3 runs
│           ├── validation_20251015_191319.json ← Individual run (latest)
│           ├── validation_20251015_185827.json ← Individual run
│           └── validation_20251015_141810.json ← Individual run (oldest)
│
├── context_bundles/
│   ├── bundle_20251015_191326/
│   │   └── context_bundle.json
│   ├── bundle_20251015_185830/
│   │   └── context_bundle.json
│   └── bundle_20251015_141813/
│       └── context_bundle.json
│
├── enhanced_analysis/
│   ├── enhanced_analysis_20251015_191326.json
│   ├── enhanced_analysis_20251015_185830.json
│   └── enhanced_analysis_20251015_141813.json
│
├── llm_output/
│   ├── llm_output_20251015_191326.json
│   ├── llm_output_20251015_185830.json
│   └── llm_output_20251015_141813.json
│
└── reports/
    ├── run_20251015_191319_..._report.md
    ├── run_20251015_185827_..._report.md
    └── run_20251015_141810_..._report.md
```

**Notice:**
- ✅ **One** `run_history.json` per service/environment
- ✅ Contains **all** runs in one file (up to 50)
- ✅ Individual `validation_*.json` files also exist (for backward compatibility)

---

## 🎯 **File Name Pattern**

| File Type | Pattern | Count | Purpose |
|-----------|---------|-------|---------|
| **Run History** | `run_history.json` | **1 per service/env** | Stores ALL runs for UI |
| **Validation Result** | `validation_{timestamp}.json` | **1 per run** | Individual run details |
| **Context Bundle** | `bundle_{timestamp}/context_bundle.json` | **1 per run** | Config diff data |
| **Enhanced Analysis** | `enhanced_analysis_{timestamp}.json` | **1 per run** | AI analysis |
| **LLM Output** | `llm_output_{timestamp}.json` | **1 per run** | LLM format data |
| **Report** | `run_{timestamp}_{id}_report.md` | **1 per run** | Human-readable report |

---

## 💡 **Why One File Per Service/Environment?**

### **Pros:**
- ✅ **Fast to load** - Single API call gets all runs
- ✅ **Easy to query** - One file to read
- ✅ **Atomic updates** - File write is atomic operation
- ✅ **Simple cleanup** - Just limit array size

### **Alternative (Not Used):**
We could have created one file per run:
```
run_20251015_191319_metadata.json
run_20251015_185827_metadata.json
run_20251015_141810_metadata.json
```

But that would require:
- ❌ Multiple API calls to load all runs
- ❌ More complex file management
- ❌ Harder to sort by date

---

## 🔄 **How the File Updates**

### **First Analysis:**

```json
// run_history.json created
{
  "service_id": "cxp_credit_services",
  "environment": "prod",
  "runs": [
    { "run_id": "run_20251015_141810_...", ... }
  ]
}
```

### **Second Analysis:**

```json
// run_history.json updated
{
  "service_id": "cxp_credit_services",
  "environment": "prod",
  "runs": [
    { "run_id": "run_20251015_185827_...", ... },  ← Newest (inserted at position 0)
    { "run_id": "run_20251015_141810_...", ... }   ← Older
  ]
}
```

### **Third Analysis:**

```json
// run_history.json updated
{
  "service_id": "cxp_credit_services",
  "environment": "prod",
  "runs": [
    { "run_id": "run_20251015_191319_...", ... },  ← Newest
    { "run_id": "run_20251015_185827_...", ... },
    { "run_id": "run_20251015_141810_...", ... }   ← Oldest
  ]
}
```

**Pattern:** New runs are **inserted at the beginning** (position 0), so newest is always first.

---

## 🧪 **How to Check If It Was Created**

### **After running an analysis, check:**

```bash
# Check if file exists
ls -la "config_data/service_results/cxp_credit_services/prod/run_history.json"

# View the file
cat "config_data/service_results/cxp_credit_services/prod/run_history.json"

# Pretty print
cat "config_data/service_results/cxp_credit_services/prod/run_history.json" | python -m json.tool
```

### **Expected Output:**

```json
{
  "service_id": "cxp_credit_services",
  "environment": "prod",
  "runs": [
    {
      "run_id": "run_20251015_191319_cxp_credit_services_prod_analysis_1760569994",
      "timestamp": "2025-10-15T19:13:19Z",
      "execution_time_seconds": 42.18,
      "verdict": "WARN",
      "branches": {
        "main_branch": "main",
        "golden_branch": "golden_prod_20251015_185719_83ed47",
        "drift_branch": "drift_prod_20251015_191324_3075b4"
      },
      "metrics": {
        "files_analyzed": 53,
        "files_with_drift": 3,
        "total_deltas": 37,
        "policy_violations": 1,
        "critical_violations": 0,
        "high_violations": 1,
        "overall_risk_level": "medium"
      },
      "file_paths": {
        "context_bundle": "...",
        "enhanced_analysis": "...",
        "llm_output": "...",
        "report": "..."
      },
      "summary": {
        "top_issues": []
      }
    }
  ]
}
```

---

## 📊 **Complete File Locations by Service**

### **For 3 Services × 4 Environments = 12 Files:**

```
config_data/service_results/
├── cxp_credit_services/
│   ├── prod/run_history.json         ← Stores all prod runs
│   ├── dev/run_history.json          ← Stores all dev runs
│   ├── qa/run_history.json           ← Stores all qa runs
│   └── staging/run_history.json      ← Stores all staging runs
│
├── cxp_ordering_services/
│   ├── prod/run_history.json
│   ├── dev/run_history.json
│   ├── qa/run_history.json
│   └── staging/run_history.json
│
└── cxp_config_properties/
    ├── prod/run_history.json
    ├── dev/run_history.json
    ├── qa/run_history.json
    └── staging/run_history.json

Total: 12 run_history.json files (one per service/environment)
```

---

## ✅ **Quick Reference**

| Question | Answer |
|----------|--------|
| **New file created?** | ✅ YES - `run_history.json` |
| **Where?** | `config_data/service_results/{service}/{env}/` |
| **How many?** | 1 per service/environment combination |
| **File name?** | Always `run_history.json` (same name) |
| **When created?** | After first analysis for that service/env |
| **Updated when?** | After every new analysis |
| **Max runs stored?** | 50 runs per file |
| **Format?** | JSON with service_id, environment, and runs array |

---

## 🎯 **Example for cxp_credit_services / prod:**

**File Path:**
```
config_data/service_results/cxp_credit_services/prod/run_history.json
```

**Created When:**
- First time you run analysis for `cxp_credit_services` in `prod` environment

**Updated When:**
- Every time you run analysis for `cxp_credit_services` in `prod` environment

**Contains:**
- All past analysis runs for this specific service/environment combination
- Up to 50 runs (oldest are automatically deleted)

---

## 📝 **Summary**

**YES, we create a new JSON file:**
- **Name:** `run_history.json`
- **Location:** `config_data/service_results/{service_id}/{environment}/`
- **Example:** `config_data/service_results/cxp_credit_services/prod/run_history.json`
- **Count:** 1 file per service/environment (12 total for 3 services × 4 environments)
- **Contents:** Array of all runs with metadata (up to 50 runs)

It's created automatically after your first analysis and updated after every subsequent analysis! 🎉

