# 🚀 Implementation: Run History in Change History Tab

**Feature:** Show all past analysis runs in the Change History tab  
**Status:** 📋 Implementation Plan  
**Replaces:** Mock data in Change History tab

---

## 🎯 **Goal**

Transform the "Change History" tab from **mock data** to **real run history**:

```
Before (Mock):
┌─────────────────────────────────────────┐
│ Change History                          │
├─────────────────────────────────────────┤
│ a1b2c3d4          [Deployed]            │
│ production • 2 hours ago • Sarah Chen   │  ← Fake data
│ feat: update session timeout config     │
└─────────────────────────────────────────┘

After (Real):
┌─────────────────────────────────────────┐
│ Analysis History                        │
├─────────────────────────────────────────┤
│ Run #3            [⚠️ WARN]             │
│ Oct 15, 19:13 • 3 files drifted         │  ← Real data
│ Golden: golden_prod_20251015_185719     │
│ Click to view detailed analysis →       │  ← Clickable!
└─────────────────────────────────────────┘
```

---

## 📋 **What to Store for Each Run**

### **Run Metadata JSON Structure**

Create a new file for each run with all metadata:

```json
// config_data/service_results/cxp_credit_services/prod/run_history.json
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
        "context_bundle": "config_data/context_bundles/bundle_20251015_191326/context_bundle.json",
        "enhanced_analysis": "config_data/enhanced_analysis/enhanced_analysis_20251015_191326.json",
        "llm_output": "config_data/llm_output/llm_output_20251015_191326.json",
        "report": "config_data/reports/run_20251015_191319_..._report.md",
        "stored_result": "config_data/service_results/cxp_credit_services/prod/validation_20251015_191319.json"
      },
      
      "summary": {
        "drift_types": ["config_change", "dependency_update"],
        "affected_files": ["application.yml", "pom.xml"],
        "top_issues": [
          "Database connection pool size changed",
          "New dependency added without review"
        ]
      }
    },
    {
      "run_id": "run_20251015_185827_cxp_credit_services_prod_analysis_1760569065",
      "timestamp": "2025-10-15T18:58:27Z",
      "execution_time_seconds": 45.3,
      "verdict": "WARN",
      // ... same structure
    }
  ]
}
```

---

## 🔧 **Implementation Steps**

### **Step 1: Backend - Save Run Metadata**

Add function to save run history in `main.py`:

```python
# main.py - Add after store_service_result()

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
        except:
            pass
    
    # Extract run metadata
    run_metadata = {
        "run_id": run_data.get("run_id"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "execution_time_seconds": run_data.get("execution_time_ms", 0) / 1000,
        "verdict": run_data.get("verdict", "UNKNOWN"),
        
        "branches": {
            "main_branch": run_data.get("request_params", {}).get("main_branch"),
            "golden_branch": run_data.get("golden_branch"),  # Need to extract this
            "drift_branch": run_data.get("drift_branch")      # Need to extract this
        },
        
        "metrics": {
            "files_analyzed": run_data.get("files_analyzed", 0),
            "files_with_drift": run_data.get("files_with_drift", 0),
            "total_deltas": run_data.get("total_deltas", 0),
            "policy_violations": run_data.get("policy_violations_count", 0),
            "critical_violations": run_data.get("critical_violations", 0),
            "high_violations": run_data.get("high_violations", 0),
            "overall_risk_level": run_data.get("overall_risk_level", "unknown")
        },
        
        "file_paths": run_data.get("file_paths", {}),
        
        "summary": {
            "drift_types": [],  # Extract from deltas
            "affected_files": [],  # Extract from analysis
            "top_issues": []  # Extract from policy violations
        }
    }
    
    # Add to beginning of runs list (newest first)
    history["runs"].insert(0, run_metadata)
    
    # Keep only last 20 runs
    history["runs"] = history["runs"][:20]
    
    # Save updated history
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, default=str)
    
    print(f"✅ Saved run history for {service_id}/{environment}")


# Update store_service_result() to also save history
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
        
        # NEW: Also save to run history
        save_run_history(service_id, environment, result)
        
        # Keep only the 5 most recent results per service/environment
        cleanup_old_results(service_results_dir, keep_count=5)
        
    except Exception as e:
        print(f"⚠️ Could not store result for {service_id}/{environment}: {e}")
```

---

### **Step 2: Backend - API Endpoint for Run History**

Add new endpoint to fetch run history:

```python
# main.py - Add new endpoint

@app.get("/api/services/{service_id}/run-history/{environment}")
async def get_run_history(service_id: str, environment: str):
    """Get run history for a specific service/environment"""
    if service_id not in SERVICES_CONFIG:
        raise HTTPException(404, f"Service {service_id} not found")
    
    config = SERVICES_CONFIG[service_id]
    if environment not in config["environments"]:
        raise HTTPException(400, f"Invalid environment '{environment}'")
    
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
                        # Load the detailed result file
                        result_file = run["file_paths"].get("stored_result")
                        if result_file and Path(result_file).exists():
                            with open(result_file, 'r', encoding='utf-8') as rf:
                                detailed_result = json.load(rf)
                            return detailed_result
                        else:
                            return run  # Return metadata at least
            except Exception as e:
                continue
    
    raise HTTPException(404, f"Run {run_id} not found for service {service_id}")
```

---

### **Step 3: Frontend - Update Change History Tab**

Replace mock data with real run history in `branch_env.html`:

```javascript
// branch_env.html - Replace HistoryTab function

function HistoryTab({serviceId, environment}) {
  const [runHistory, setRunHistory] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(null);
  
  // Load run history from API
  React.useEffect(() => {
    const loadRunHistory = async () => {
      try {
        setLoading(true);
        const response = await fetch(`/api/services/${serviceId}/run-history/${environment}`);
        if (!response.ok) throw new Error('Failed to load run history');
        const data = await response.json();
        setRunHistory(data.runs || []);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    
    if (serviceId && environment) {
      loadRunHistory();
    }
  }, [serviceId, environment]);
  
  // Format timestamp
  const formatTimestamp = (isoString) => {
    const date = new Date(isoString);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };
  
  // Get verdict badge style
  const getVerdictStyle = (verdict) => {
    const styles = {
      'PASS': { bg: 'var(--green)', text: '✅ PASS' },
      'WARN': { bg: 'var(--yellow)', text: '⚠️ WARN' },
      'REVIEW_REQUIRED': { bg: 'var(--orange)', text: '🔍 REVIEW' },
      'BLOCK': { bg: 'var(--red)', text: '🚫 BLOCK' },
      'COMPLETED': { bg: 'var(--blue)', text: '✅ COMPLETED' }
    };
    return styles[verdict] || { bg: 'var(--muted)', text: verdict };
  };
  
  // Handle click to view run details
  const handleViewRun = (run) => {
    // Open service detail page with run ID in query params
    window.location.href = `/service/${serviceId}?run_id=${run.run_id}&env=${environment}`;
  };
  
  if (loading) {
    return e('div', {className: 'card', style: {textAlign: 'center', padding: '40px'}}, [
      e('div', {style: {fontSize: '24px', marginBottom: '16px'}}, '⏳'),
      e('div', null, 'Loading analysis history...')
    ]);
  }
  
  if (error) {
    return e('div', {className: 'card', style: {textAlign: 'center', padding: '40px'}}, [
      e('div', {style: {fontSize: '24px', marginBottom: '16px'}}, '❌'),
      e('div', null, `Error: ${error}`)
    ]);
  }
  
  if (runHistory.length === 0) {
    return e('div', {className: 'card', style: {textAlign: 'center', padding: '40px'}}, [
      e('div', {style: {fontSize: '24px', marginBottom: '16px'}}, '📭'),
      e('div', null, 'No analysis runs yet'),
      e('div', {style: {color: 'var(--muted)', marginTop: '8px'}}, 
        'Run an analysis to see results here')
    ]);
  }
  
  return e('div', {className: 'card'}, [
    e('h3', {style: {margin: '0 0 20px 0'}}, 
      `Analysis History (${runHistory.length} runs)`),
    
    // Run list
    ...runHistory.map((run, index) => {
      const verdictStyle = getVerdictStyle(run.verdict);
      
      return e('div', {
        key: run.run_id,
        className: 'commit-item',
        style: {
          cursor: 'pointer',
          transition: 'all 0.2s',
          borderLeft: `4px solid ${verdictStyle.bg}`
        },
        onClick: () => handleViewRun(run),
        onMouseEnter: (e) => {
          e.currentTarget.style.background = '#f8f9fa';
          e.currentTarget.style.transform = 'translateX(4px)';
        },
        onMouseLeave: (e) => {
          e.currentTarget.style.background = 'transparent';
          e.currentTarget.style.transform = 'translateX(0)';
        }
      }, [
        // Header row
        e('div', {style: {display: 'flex', justifyContent: 'space-between', marginBottom: '8px'}}, [
          e('div', null, [
            e('strong', {style: {fontSize: '16px'}}, `Run #${runHistory.length - index}`),
            e('span', {style: {color: 'var(--muted)', marginLeft: '12px'}}, 
              formatTimestamp(run.timestamp))
          ]),
          e('span', {
            className: 'badge',
            style: {background: verdictStyle.bg, color: 'white'}
          }, verdictStyle.text)
        ]),
        
        // Metrics row
        e('div', {className: 'commit-meta', style: {marginBottom: '4px'}}, [
          `${run.metrics.files_with_drift} files drifted • `,
          `${run.metrics.total_deltas} changes • `,
          `${run.metrics.policy_violations} violations • `,
          `Risk: ${run.metrics.overall_risk_level}`
        ]),
        
        // Branches row
        e('div', {style: {fontSize: '12px', color: 'var(--muted)', marginBottom: '8px'}}, [
          `Golden: ${run.branches.golden_branch || 'N/A'}`,
          e('br'),
          `Drift: ${run.branches.drift_branch || 'N/A'}`
        ]),
        
        // Execution time
        e('div', {style: {fontSize: '12px', color: 'var(--muted)'}}, 
          `Execution time: ${run.execution_time_seconds.toFixed(1)}s`),
        
        // View link
        e('div', {
          style: {
            marginTop: '12px',
            color: 'var(--primary)',
            fontSize: '14px',
            fontWeight: '500'
          }
        }, '→ Click to view detailed analysis')
      ]);
    })
  ]);
}
```

---

### **Step 4: Update Tab Rendering to Pass Props**

Update the tab rendering in `branch_env.html`:

```javascript
// branch_env.html - Update activeTab rendering

// Replace this line:
activeTab === 'history' && e(HistoryTab, {issueData}),

// With this:
activeTab === 'history' && e(HistoryTab, {serviceId, environment: 'prod'}),
// Note: For now using 'prod', but should be dynamic based on current view
```

---

### **Step 5: Handle Run Selection in Service Detail Page**

Update `index.html` or service detail page to load specific run:

```javascript
// index.html or service-detail page - Check for run_id in URL

React.useEffect(() => {
  const urlParams = new URLSearchParams(window.location.search);
  const runId = urlParams.get('run_id');
  
  if (runId) {
    // Load specific run data instead of latest
    fetch(`/api/services/${serviceId}/run/${runId}`)
      .then(res => res.json())
      .then(data => {
        // Display this specific run's data
        setAnalysisData(data);
      });
  } else {
    // Load latest run (current behavior)
    // ... existing code
  }
}, [serviceId]);
```

---

## 📊 **Visual Design**

### **Change History Tab (New Design)**

```
┌───────────────────────────────────────────────────────────────┐
│ Analysis History (15 runs)                                    │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Run #15              Oct 15, 19:13      [⚠️ WARN]       │ │
│ │ 3 files drifted • 37 changes • 1 violation • Risk: medium│ │
│ │ Golden: golden_prod_20251015_185719                      │ │
│ │ Drift: drift_prod_20251015_191324                        │ │
│ │ Execution time: 42.2s                                    │ │
│ │ → Click to view detailed analysis                        │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                               │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Run #14              Oct 15, 18:58      [⚠️ WARN]       │ │
│ │ 2 files drifted • 28 changes • 0 violations • Risk: low  │ │
│ │ Golden: golden_prod_20251015_185719                      │ │
│ │ Drift: drift_prod_20251015_110848                        │ │
│ │ Execution time: 45.3s                                    │ │
│ │ → Click to view detailed analysis                        │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                               │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Run #13              Oct 15, 14:22      [✅ PASS]       │ │
│ │ 0 files drifted • 0 changes • 0 violations • Risk: none  │ │
│ │ Golden: golden_prod_20251015_142015                      │ │
│ │ Drift: drift_prod_20251015_142201                        │ │
│ │ Execution time: 38.1s                                    │ │
│ │ → Click to view detailed analysis                        │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

---

## 🎯 **Benefits of This Approach**

1. ✅ **Historical Tracking** - See all past analyses
2. ✅ **Quick Comparison** - Compare metrics across runs
3. ✅ **Easy Access** - Click to view detailed analysis
4. ✅ **Replaces Mock Data** - Makes tab useful
5. ✅ **Audit Trail** - Know when each analysis ran
6. ✅ **Trend Analysis** - See if drift is increasing/decreasing

---

## 📋 **Implementation Checklist**

- [ ] **Backend: Add `save_run_history()` function**
- [ ] **Backend: Update `store_service_result()` to call `save_run_history()`**
- [ ] **Backend: Add `/api/services/{id}/run-history/{env}` endpoint**
- [ ] **Backend: Add `/api/services/{id}/run/{run_id}` endpoint**
- [ ] **Frontend: Replace `HistoryTab` function with new version**
- [ ] **Frontend: Update tab rendering to pass props**
- [ ] **Frontend: Add run_id URL parameter handling in service detail page**
- [ ] **Test: Run analysis and verify history is saved**
- [ ] **Test: Verify history displays in UI**
- [ ] **Test: Click run and verify detail page opens**

---

## 🚀 **Quick Start (Minimal Implementation)**

If you want to start simple, here's the minimal version:

1. **Just save run_id, timestamp, verdict in a JSON file**
2. **Create basic API endpoint to return that JSON**
3. **Update HistoryTab to display it**
4. **Add click handler to open service detail page**

Then enhance with more metadata later!

---

## ✅ **Summary**

Your idea transforms a **useless mock tab** into a **powerful historical analysis viewer**!

**What it gives you:**
- 📊 See all past analysis runs
- 🔍 Click to view detailed results
- 📈 Track trends over time
- 🎯 Quick access to any past run
- ✅ Makes the UI much more useful

**This is a great enhancement!** 🎉

