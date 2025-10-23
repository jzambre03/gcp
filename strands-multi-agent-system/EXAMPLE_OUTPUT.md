# 📊 Inference API - Example Output

## Sample API Call

```bash
curl -X POST http://localhost:3000/api/inference \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "cxp_ptg_adapter",
    "environment": "alpha"
  }'
```

---

## ✅ Example Success Response

### **JSON Output:**

```json
{
  "status": "success",
  "service_name": "cxp_ptg_adapter",
  "environment": "alpha",
  "timestamp": "2025-10-23T18:45:32.123Z",
  "run_id": "run_20251023_184532_cxp_ptg_adapter_alpha_inference_1729709132",
  "metrics": {
    "total_config_files": 42,
    "files_with_drift": 8,
    "total_drifts": 15,
    "high_risk_drifts": 0,
    "medium_risk_drifts": 5,
    "low_risk_drifts": 10,
    "allowed_variance": 0,
    "overall_risk_level": "MEDIUM"
  },
  "execution_time_seconds": 45.67,
  "analysis_url": "http://localhost:3000/branch-environment?id=cxp_ptg_adapter&run_id=run_20251023_184532_cxp_ptg_adapter_alpha_inference_1729709132&tab=deployment"
}
```

### **Server Console Output:**

```
================================================================================
🤖 INFERENCE API REQUEST
================================================================================
📋 Service Name: cxp_ptg_adapter
🌍 Environment: alpha
📦 Repository: https://gitlab.verizon.com/saja9l7/cxp-ptg-adapter.git
🌿 Main Branch: main
================================================================================
🔄 Running drift analysis...
================================================================================

[... analysis logs ...]

================================================================================
✅ INFERENCE COMPLETED
================================================================================
📊 Total Config Files:    42
📁 Files with Drift:      8
🔍 Total Drifts:          15
   ├─ ⚠️  High Risk:       0
   ├─ ⚡ Medium Risk:      5
   ├─ ℹ️  Low Risk:        10
   └─ ✅ Allowed:          0
🎯 Overall Risk Level:    MEDIUM
⏱️  Execution Time:        45.67s
🔗 View Details:          http://localhost:3000/branch-environment?id=cxp_ptg_adapter&run_id=run_20251023_184532_cxp_ptg_adapter_alpha_inference_1729709132&tab=deployment
================================================================================
```

---

## 📝 Python Test Script Output

```bash
python test_inference_api.py cxp_ptg_adapter alpha
```

**Output:**

```
================================================================================
🤖 Testing Inference API
================================================================================
📋 Service: cxp_ptg_adapter
🌍 Environment: alpha
🌐 API URL: http://localhost:3000/api/inference
================================================================================

📤 Sending request...
Payload: {
  "service_name": "cxp_ptg_adapter",
  "environment": "alpha"
}

✅ SUCCESS!
================================================================================

📊 Analysis Results:
--------------------------------------------------------------------------------
Service:          cxp_ptg_adapter
Environment:      alpha
Run ID:           run_20251023_184532_cxp_ptg_adapter_alpha_inference_1729709132
Timestamp:        2025-10-23T18:45:32.123Z
Execution Time:   45.67s

📁 File Analysis:
Total Config Files:    42
Files with Drift:      8

🔍 Drift Breakdown:
Total Drifts:          15
   ├─ ⚠️  High Risk:    0
   ├─ ⚡ Medium Risk:   5
   ├─ ℹ️  Low Risk:     10
   └─ ✅ Allowed:       0

🎯 Overall Risk Level: MEDIUM

🔗 View Full Details:
   http://localhost:3000/branch-environment?id=cxp_ptg_adapter&run_id=run_20251023_184532_cxp_ptg_adapter_alpha_inference_1729709132&tab=deployment
--------------------------------------------------------------------------------

💾 Full response saved to: inference_result_cxp_ptg_adapter_alpha.json
```

---

## 🚨 Example Error Responses

### **Invalid Service (404):**

**Request:**
```bash
curl -X POST http://localhost:3000/api/inference \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "invalid_service",
    "environment": "alpha"
  }'
```

**Response:**
```json
{
  "detail": {
    "error": "Service 'invalid_service' not found",
    "available_services": ["cxp_ptg_adapter"],
    "hint": "Use one of: cxp_ptg_adapter"
  }
}
```

---

### **Invalid Environment (400):**

**Request:**
```bash
curl -X POST http://localhost:3000/api/inference \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "cxp_ptg_adapter",
    "environment": "staging"
  }'
```

**Response:**
```json
{
  "detail": {
    "error": "Invalid environment 'staging' for service 'cxp_ptg_adapter'",
    "valid_environments": ["prod", "alpha", "beta1", "beta2"],
    "hint": "Use one of: prod, alpha, beta1, beta2"
  }
}
```

---

## 📈 Zero Drift Example

**Request:**
```bash
curl -X POST http://localhost:3000/api/inference \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "cxp_ptg_adapter",
    "environment": "prod"
  }'
```

**Response:**
```json
{
  "status": "success",
  "service_name": "cxp_ptg_adapter",
  "environment": "prod",
  "timestamp": "2025-10-23T18:50:15.456Z",
  "run_id": "run_20251023_185015_cxp_ptg_adapter_prod_inference_1729709415",
  "metrics": {
    "total_config_files": 38,
    "files_with_drift": 0,
    "total_drifts": 0,
    "high_risk_drifts": 0,
    "medium_risk_drifts": 0,
    "low_risk_drifts": 0,
    "allowed_variance": 0,
    "overall_risk_level": "NONE"
  },
  "execution_time_seconds": 32.14,
  "analysis_url": "http://localhost:3000/branch-environment?id=cxp_ptg_adapter&run_id=run_20251023_185015_cxp_ptg_adapter_prod_inference_1729709415&tab=deployment"
}
```

---

## 💡 Key Takeaways

### **What You Get:**

✅ **Metadata Only** - No bulky drift details, just the metrics  
✅ **File Statistics** - Total files compared and files with drifts  
✅ **Drift Breakdown** - Count by risk level (high/medium/low/allowed)  
✅ **Overall Assessment** - Single risk level (HIGH/MEDIUM/LOW/NONE)  
✅ **Direct Link** - URL to view full analysis in web UI  
✅ **Fast Response** - Clean, compact JSON for quick parsing  

### **What You Don't Get:**

❌ Full validation result object  
❌ Detailed drift content (old/new values)  
❌ Individual drift explanations  
❌ Policy violation details  

**All detailed information is available by clicking the `analysis_url`!**

---

## 🔗 Using the Analysis URL

The `analysis_url` takes you directly to the **Drift Analysis tab** where you can:

1. **View all drifts** organized by risk level
2. **See exact changes** with old vs new values
3. **Read AI explanations** for each drift
4. **Get remediation tips** from Claude 3.5 Sonnet
5. **Export results** for reporting
6. **Share with team** using the URL

**Example URL:**
```
http://localhost:3000/branch-environment?id=cxp_ptg_adapter&run_id=run_20251023_184532_cxp_ptg_adapter_alpha_inference_1729709132&tab=deployment
```

**URL Parameters:**
- `id` - Service identifier
- `run_id` - Unique analysis run identifier
- `tab` - Opens directly to "deployment" (Drift Analysis) tab

---

## 🎯 Perfect For:

- ✅ **CI/CD Pipelines** - Gate deployments based on drift metrics
- ✅ **Monitoring Systems** - Track drift trends over time
- ✅ **Dashboards** - Display key metrics across environments
- ✅ **Alerting** - Trigger alerts on high-risk drifts
- ✅ **Reporting** - Generate executive summaries
- ✅ **APIs** - Integrate with other tools and systems

---

**Last Updated:** October 23, 2025  
**API Version:** 1.0  
**Endpoint:** `POST /api/inference`

