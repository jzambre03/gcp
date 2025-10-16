# 📄 Display Config Files in UI - Implementation Guide

**Question:** Can we display config files in UI without downloading?  
**Answer:** ✅ **YES! Multiple ways to do this**

---

## 🎯 **What You Can Display**

Your system already captures this data:

1. ✅ **File diffs (patches)** - Unified diff format showing changes
2. ✅ **Old vs New values** - In deltas with old/new fields  
3. ✅ **Full file contents** - Can fetch from Git or bundles
4. ✅ **Line numbers** - Precise locations of changes

---

## 🚀 **Option 1: Display Diffs (RECOMMENDED - EASIEST)**

Your system already creates **patch files** during analysis!

### **What's Available:**

```
config_data/
└── context_bundles/
    └── bundle_20251015_191326/
        ├── context_bundle.json
        └── patches/                        ← Patch files stored here!
            ├── helm__config-map__application-vcgbeta1.yml.patch
            ├── pom.xml.patch
            └── src__main__resources__application.properties.patch
```

Each `.patch` file contains:
```diff
--- a/helm/config-map/application-vcgbeta1.yml
+++ b/helm/config-map/application-vcgbeta1.yml
@@ -15,7 +15,7 @@
   profile: vcgbeta1
   
 # Security Settings
-ACCOUNT_PIN_ENABLED: True
+ACCOUNT_PIN_ENABLED: False    ← Changed!
 
-SSN_TOKENIZE_ENABLED: True
+SSN_TOKENIZE_ENABLED: False   ← Changed!
```

---

## 🔧 **Implementation: Display Diffs in UI**

### **Step 1: Backend - Add File Content API**

```python
# main.py - Add new endpoint

@app.get("/api/services/{service_id}/file-diff/{run_id}/{file_path:path}")
async def get_file_diff(service_id: str, run_id: str, file_path: str):
    """Get file diff/patch for a specific file in a run"""
    if service_id not in SERVICES_CONFIG:
        raise HTTPException(404, f"Service {service_id} not found")
    
    # Find the run to get its context_bundle path
    for env in SERVICES_CONFIG[service_id]["environments"]:
        history_file = Path("config_data") / "service_results" / service_id / env / "run_history.json"
        
        if history_file.exists():
            with open(history_file, 'r') as f:
                history = json.load(f)
            
            for run in history["runs"]:
                if run["run_id"] == run_id:
                    # Get context_bundle path
                    bundle_path = run["file_paths"].get("context_bundle")
                    if not bundle_path:
                        raise HTTPException(404, "Context bundle not found")
                    
                    # Load context_bundle
                    with open(bundle_path, 'r') as bf:
                        bundle = json.load(bf)
                    
                    # Check if patches exist
                    bundle_dir = Path(bundle_path).parent
                    patches_dir = bundle_dir / "patches"
                    
                    # Convert file path to patch filename
                    safe_name = file_path.replace("/", "__")
                    patch_file = patches_dir / f"{safe_name}.patch"
                    
                    if patch_file.exists():
                        # Return the patch
                        with open(patch_file, 'r') as pf:
                            patch_content = pf.read()
                        
                        return {
                            "file": file_path,
                            "type": "patch",
                            "content": patch_content,
                            "format": "unified_diff"
                        }
                    else:
                        # No patch, find the delta to show old/new values
                        deltas = bundle.get("deltas", [])
                        file_deltas = [d for d in deltas if d.get("file") == file_path]
                        
                        return {
                            "file": file_path,
                            "type": "deltas",
                            "deltas": file_deltas,
                            "format": "structured"
                        }
    
    raise HTTPException(404, f"File diff not found for {file_path} in run {run_id}")


@app.get("/api/services/{service_id}/file-content/{run_id}/{file_path:path}")
async def get_file_content(service_id: str, run_id: str, file_path: str, version: str = "new"):
    """
    Get full file content for a specific file in a run.
    
    Args:
        version: 'old' (golden) or 'new' (drift)
    """
    # This would read the actual file from the context bundle or cloned repo
    # More complex - implement if needed
    raise HTTPException(501, "Full file content endpoint not implemented yet")
```

---

### **Step 2: Frontend - Add File Viewer Component**

Add to `branch_env.html` or service detail page:

```javascript
function FileViewer({fileName, runId, serviceId}) {
  const [fileData, setFileData] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(null);
  
  React.useEffect(() => {
    const loadFile = async () => {
      try {
        setLoading(true);
        const response = await fetch(`/api/services/${serviceId}/file-diff/${runId}/${encodeURIComponent(fileName)}`);
        if (!response.ok) throw new Error('Failed to load file');
        const data = await response.json();
        setFileData(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    loadFile();
  }, [fileName, runId, serviceId]);
  
  if (loading) return e('div', null, '⏳ Loading...');
  if (error) return e('div', null, `❌ Error: ${error}`);
  
  // Display patch (diff format)
  if (fileData.type === 'patch') {
    return e('div', {className: 'file-viewer'}, [
      e('h4', null, `📄 ${fileName}`),
      e('pre', {
        style: {
          background: '#f5f5f5',
          padding: '16px',
          borderRadius: '8px',
          overflow: 'auto',
          fontSize: '14px',
          fontFamily: 'monospace',
          lineHeight: '1.5'
        }
      }, formatDiff(fileData.content))
    ]);
  }
  
  // Display deltas (structured format)
  if (fileData.type === 'deltas') {
    return e('div', {className: 'file-viewer'}, [
      e('h4', null, `📄 ${fileName}`),
      fileData.deltas.map(delta => 
        e('div', {
          key: delta.id,
          style: {
            background: '#f5f5f5',
            padding: '12px',
            marginBottom: '8px',
            borderRadius: '6px',
            borderLeft: '4px solid var(--yellow)'
          }
        }, [
          e('div', {style: {fontWeight: 'bold', marginBottom: '8px'}}, 
            delta.locator.value),
          e('div', {style: {display: 'flex', gap: '24px'}}, [
            e('div', null, [
              e('span', {style: {color: 'var(--red)'}}, '- Old: '),
              e('code', null, JSON.stringify(delta.old))
            ]),
            e('div', null, [
              e('span', {style: {color: 'var(--green)'}}, '+ New: '),
              e('code', null, JSON.stringify(delta.new))
            ])
          ])
        ])
      )
    ]);
  }
}

// Helper function to format diff with colors
function formatDiff(patchContent) {
  // Color-code the diff lines
  const lines = patchContent.split('\n');
  return lines.map((line, i) => {
    const style = {};
    if (line.startsWith('+') && !line.startsWith('+++')) {
      style.color = 'var(--green)';
      style.background = '#e6ffed';
    } else if (line.startsWith('-') && !line.startsWith('---')) {
      style.color = 'var(--red)';
      style.background = '#ffebe9';
    } else if (line.startsWith('@@')) {
      style.color = 'var(--blue)';
      style.fontWeight = 'bold';
    }
    
    return e('div', {key: i, style}, line);
  });
}
```

---

### **Step 3: Add File List to Analysis History**

Update the `HistoryTab` to show which files changed:

```javascript
// In HistoryTab, for each run:
e('div', {style: {marginTop: '12px'}}, [
  e('strong', {style: {fontSize: '12px', color: 'var(--muted)'}}, 
    'Files Changed:'),
  e('div', {style: {marginTop: '4px', display: 'flex', flexWrap: 'wrap', gap: '4px'}}, 
    (run.summary.affected_files || []).map(file => 
      e('button', {
        key: file,
        className: 'btn',
        style: {fontSize: '11px', padding: '4px 8px'},
        onClick: (e) => {
          e.stopPropagation();
          showFileViewer(file, run.run_id);
        }
      }, file)
    )
  )
])
```

---

## 🎨 **Visual Design**

### **Option A: Modal Popup** (Clean)

```
┌─────────────────────────────────────────────────────────────┐
│ Run #15    Oct 15, 19:13    [⚠️ WARN]                       │
│ 3 files drifted • 37 changes                                │
│                                                             │
│ Files Changed:                                              │
│ [application-vcgbeta1.yml] [pom.xml] [application.properties]│
│     ↓ Click                                                 │
└─────────────────────────────────────────────────────────────┘

Clicks "application-vcgbeta1.yml" →

┌──────────────────────────── MODAL ──────────────────────────┐
│                                                      [✕ Close]│
│ 📄 helm/config-map/application-vcgbeta1.yml                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  --- a/helm/config-map/application-vcgbeta1.yml            │
│  +++ b/helm/config-map/application-vcgbeta1.yml            │
│  @@ -15,7 +15,7 @@                                         │
│    profile: vcgbeta1                                        │
│                                                             │
│  - ACCOUNT_PIN_ENABLED: True                               │
│  + ACCOUNT_PIN_ENABLED: False     ← Red background         │
│                                                             │
│  - SSN_TOKENIZE_ENABLED: True                              │
│  + SSN_TOKENIZE_ENABLED: False    ← Red background         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### **Option B: Expandable Section** (Inline)

```
┌─────────────────────────────────────────────────────────────┐
│ Run #15    Oct 15, 19:13    [⚠️ WARN]          [▼ Expand]  │
│ 3 files drifted • 37 changes                                │
└─────────────────────────────────────────────────────────────┘
       ↓ Click Expand

┌─────────────────────────────────────────────────────────────┐
│ Run #15    Oct 15, 19:13    [⚠️ WARN]          [▲ Collapse]│
│ 3 files drifted • 37 changes                                │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 📄 helm/config-map/application-vcgbeta1.yml           │ │
│ │                                                         │ │
│ │  - ACCOUNT_PIN_ENABLED: True                           │ │
│ │  + ACCOUNT_PIN_ENABLED: False                          │ │
│ │                                                         │ │
│ │  - SSN_TOKENIZE_ENABLED: True                          │ │
│ │  + SSN_TOKENIZE_ENABLED: False                         │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 **RECOMMENDED: Quick Implementation**

### **Display Changed Values (No Additional Backend Needed!)**

You already have the data in `llm_output` and `analyzed_deltas`! Just display it in the UI:

```javascript
// Add to HistoryTab - expand each run to show changes

function RunItem({run, index, totalRuns, onViewDetails}) {
  const [expanded, setExpanded] = React.useState(false);
  
  return e('div', {className: 'commit-item'}, [
    // Header (existing code)
    e('div', {
      style: {display: 'flex', justifyContent: 'space-between'},
      onClick: () => setExpanded(!expanded)
    }, [
      e('strong', null, `Run #${totalRuns - index}`),
      e('span', null, expanded ? '▼ Collapse' : '▶ Expand')
    ]),
    
    // Expandable content - show changed values
    expanded && e('div', {
      style: {
        marginTop: '16px',
        padding: '12px',
        background: '#f8f9fa',
        borderRadius: '6px'
      }
    }, [
      e('h5', {style: {margin: '0 0 12px 0'}}, 'Configuration Changes:'),
      
      // Show top issues
      (run.summary.top_issues || []).map((issue, i) => 
        e('div', {
          key: i,
          style: {
            padding: '8px',
            marginBottom: '8px',
            background: 'white',
            borderRadius: '4px',
            borderLeft: '3px solid var(--yellow)'
          }
        }, [
          e('div', {style: {fontSize: '14px', fontWeight: '500'}}, issue),
        ])
      ),
      
      // Button to view full details
      e('button', {
        className: 'btn',
        style: {marginTop: '12px'},
        onClick: (e) => {
          e.stopPropagation();
          onViewDetails(run);
        }
      }, 'View Full Analysis →')
    ])
  ]);
}
```

---

## 🚀 **Advanced: Display Full Diffs with Syntax Highlighting**

### **Step 1: Add Diff API Endpoint**

```python
# main.py

@app.get("/api/files/patch/{bundle_id}/{file_path:path}")
async def get_file_patch(bundle_id: str, file_path: str):
    """Get patch file for a specific file from a context bundle"""
    
    # Find the bundle directory
    bundle_dir = Path("config_data") / "context_bundles" / f"bundle_{bundle_id}"
    
    if not bundle_dir.exists():
        raise HTTPException(404, "Bundle not found")
    
    # Find the patch file
    patches_dir = bundle_dir / "patches"
    safe_name = file_path.replace("/", "__")
    patch_file = patches_dir / f"{safe_name}.patch"
    
    if patch_file.exists():
        with open(patch_file, 'r') as f:
            patch_content = f.read()
        
        return {
            "file": file_path,
            "patch": patch_content,
            "bundle_id": bundle_id,
            "format": "unified_diff"
        }
    
    # If no patch file, return deltas from context_bundle
    context_bundle_file = bundle_dir / "context_bundle.json"
    if context_bundle_file.exists():
        with open(context_bundle_file, 'r') as f:
            bundle = json.load(f)
        
        # Get deltas for this file
        deltas = [d for d in bundle.get("deltas", []) if d.get("file") == file_path]
        
        return {
            "file": file_path,
            "deltas": deltas,
            "bundle_id": bundle_id,
            "format": "deltas"
        }
    
    raise HTTPException(404, f"No data found for {file_path}")


@app.get("/api/files/list/{bundle_id}")
async def get_bundle_files(bundle_id: str):
    """Get list of all changed files in a bundle"""
    
    bundle_dir = Path("config_data") / "context_bundles" / f"bundle_{bundle_id}"
    context_bundle_file = bundle_dir / "context_bundle.json"
    
    if not context_bundle_file.exists():
        raise HTTPException(404, "Bundle not found")
    
    with open(context_bundle_file, 'r') as f:
        bundle = json.load(f)
    
    file_changes = bundle.get("file_changes", {})
    
    return {
        "bundle_id": bundle_id,
        "files": {
            "modified": file_changes.get("modified", []),
            "added": file_changes.get("added", []),
            "removed": file_changes.get("removed", [])
        },
        "total_changed": len(file_changes.get("modified", [])) + 
                        len(file_changes.get("added", [])) + 
                        len(file_changes.get("removed", []))
    }
```

---

### **Step 2: Add Diff Viewer Component**

```javascript
function DiffViewer({patch, fileName}) {
  // Split into lines
  const lines = patch.split('\n');
  
  return e('div', {className: 'diff-viewer'}, [
    e('h4', {style: {
      margin: '0 0 16px 0',
      padding: '12px',
      background: '#f5f5f5',
      borderRadius: '6px'
    }}, `📄 ${fileName}`),
    
    e('div', {
      style: {
        background: 'white',
        border: '1px solid #e0e0e0',
        borderRadius: '8px',
        overflow: 'hidden'
      }
    }, [
      lines.map((line, i) => {
        let style = {
          padding: '2px 12px',
          fontFamily: 'monospace',
          fontSize: '13px',
          lineHeight: '1.6'
        };
        
        // Color code based on diff markers
        if (line.startsWith('+') && !line.startsWith('+++')) {
          style.background = '#e6ffed';
          style.color = '#24292e';
          style.borderLeft = '3px solid #28a745';
        } else if (line.startsWith('-') && !line.startsWith('---')) {
          style.background = '#ffebe9';
          style.color = '#24292e';
          style.borderLeft = '3px solid #d73a49';
        } else if (line.startsWith('@@')) {
          style.background = '#f1f8ff';
          style.color = '#0366d6';
          style.fontWeight = 'bold';
          style.padding = '8px 12px';
        } else if (line.startsWith('---') || line.startsWith('+++')) {
          style.background = '#fafbfc';
          style.color = '#6a737d';
          style.fontStyle = 'italic';
        }
        
        return e('div', {key: i, style}, line || ' ');
      })
    ])
  ]);
}
```

---

### **Step 3: Integrate into Analysis History**

```javascript
// In HistoryTab component

function RunItemWithFiles({run, index, totalRuns}) {
  const [showFiles, setShowFiles] = React.useState(false);
  const [selectedFile, setSelectedFile] = React.useState(null);
  
  return e('div', {className: 'commit-item'}, [
    // Existing run header...
    
    // Add file list button
    e('button', {
      className: 'btn',
      style: {marginTop: '12px', fontSize: '12px'},
      onClick: (e) => {
        e.stopPropagation();
        setShowFiles(!showFiles);
      }
    }, showFiles ? '▼ Hide Files' : '▶ Show Changed Files'),
    
    // File list (when expanded)
    showFiles && e('div', {style: {marginTop: '12px'}}, [
      e('div', {style: {fontSize: '13px', fontWeight: '500', marginBottom: '8px'}}, 
        'Click a file to view changes:'),
      
      // Get affected files from deltas
      ['helm/config-map/application-vcgbeta1.yml', 'pom.xml'].map(file => 
        e('div', {
          key: file,
          style: {
            padding: '8px',
            background: '#f5f5f5',
            borderRadius: '4px',
            marginBottom: '4px',
            cursor: 'pointer',
            transition: 'background 0.2s'
          },
          onClick: (e) => {
            e.stopPropagation();
            setSelectedFile(file);
          },
          onMouseEnter: (e) => e.currentTarget.style.background = '#e8e8e8',
          onMouseLeave: (e) => e.currentTarget.style.background = '#f5f5f5'
        }, [
          e('span', {style: {fontSize: '13px'}}, file),
          e('span', {style: {fontSize: '11px', color: 'var(--muted)', marginLeft: '8px'}}, 
            '→ Click to view diff')
        ])
      )
    ]),
    
    // File viewer modal
    selectedFile && e(FileViewerModal, {
      fileName: selectedFile,
      runId: run.run_id,
      serviceId: serviceId,
      onClose: () => setSelectedFile(null)
    })
  ]);
}
```

---

## 📊 **What Data is Available**

From your validation.json, you already have:

### **1. High-Level Changes**
```json
"llm_output": {
  "high": [
    {
      "file": "helm/config-map/application-vcgbeta1.yml",
      "locator": "ACCOUNT_PIN_ENABLED",
      "old": "True",
      "new": "False",
      "why": "Account PIN authentication has been disabled..."
    }
  ]
}
```

### **2. Detailed Deltas**
```json
"analyzed_deltas": [
  {
    "file": "helm/config-map/application-vcgbeta1.yml",
    "locator": { "type": "yamlpath", "value": "..." },
    "old": "True",
    "new": "False"
  }
]
```

### **3. File Patches** (if generated)
```
config_data/context_bundles/bundle_20251015_203957/patches/
└── helm__config-map__application-vcgbeta1.yml.patch
```

---

## ✅ **Simplest Implementation (5 minutes)**

Just display the old/new values from deltas **without** any new backend code:

```javascript
// In HistoryTab, add this to each run item:

e('div', {
  style: {
    marginTop: '16px',
    padding: '12px',
    background: '#f8f9fa',
    borderRadius: '6px',
    fontSize: '13px'
  }
}, [
  e('strong', null, 'Key Changes:'),
  
  // Extract from run.summary.top_issues
  (run.summary.top_issues || []).map((issue, i) => 
    e('div', {
      key: i,
      style: {
        padding: '8px',
        marginTop: '8px',
        background: 'white',
        borderRadius: '4px',
        borderLeft: '3px solid var(--yellow)'
      }
    }, [
      e('div', {style: {fontSize: '13px'}}, issue)
    ])
  )
])
```

This uses data **already in run_history.json** - no new API needed!

---

## 🎯 **My Recommendation**

### **Start Simple (Option 1):**
1. ✅ Display old/new values from run.summary.top_issues
2. ✅ No new backend code needed
3. ✅ Works immediately
4. ✅ Shows the important changes

### **Add Later (Option 2):**
1. Add API endpoint to fetch full patches
2. Add syntax-highlighted diff viewer
3. Add file browser for each run

---

**Want me to implement the simple version first (just show the changes inline)?** It would take about 5 minutes and requires no new backend code! 🚀
