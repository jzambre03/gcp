"""
LLM Format Prompt Template - EXACT MATCH to LLM_output.json

This module provides prompt templates that match the exact format
specified in UI/LLM_output.json with no extra fields.
"""

from typing import List, Dict, Any


def build_llm_format_prompt(
    file: str,
    deltas: List[Dict[str, Any]],
    environment: str = "production",
    policies: Dict[str, Any] = None
) -> str:
    """
    Build an AI prompt that returns LLM output format matching LLM_output.json EXACTLY.
    
    Args:
        file: File path being analyzed
        deltas: List of delta objects from context_bundle
        environment: Target environment (production, staging, dev, qa)
        policies: Policy rules and guidelines
    
    Returns:
        Complete prompt string for AI analysis
    
    Output Format (EXACT):
        {
          "high": [{id, file, locator, old, new, drift_category, why, ai_review_assistant, remediation}],
          "medium": [{id, file, locator, old, new, drift_category, why, ai_review_assistant, remediation}],
          "low": [{id, file, locator, old, new, drift_category, why, ai_review_assistant, remediation}],
          "allowed_variance": [{id, file, locator, old, new, drift_category, rationale}]
        }
    """
    if policies is None:
        policies = {}
    
    # Build deltas summary
    deltas_summary = []
    for idx, delta in enumerate(deltas, 1):
        locator = delta.get('locator', {})
        deltas_summary.append({
            "index": idx,
            "delta_id": delta.get('id', 'unknown'),
            "locator_type": locator.get('type', 'unknown'),
            "locator_value": locator.get('value', 'unknown'),
            "locator_extra": {k: v for k, v in locator.items() if k not in ['type', 'value']},
            "old_value": str(delta.get('old')) if delta.get('old') is not None else "null",
            "new_value": str(delta.get('new')) if delta.get('new') is not None else "null",
            "policy_tag": delta.get('policy', {}).get('tag', 'unknown'),
            "category": delta.get('category', 'unknown')
        })
    
    # Build the prompt
    prompt = f"""You are a configuration drift adjudicator analyzing file "{file}" for environment "{environment}".

Your task is to categorize ALL {len(deltas)} configuration changes into risk buckets.

## CHANGES TO ANALYZE

"""
    
    # Add each delta
    for d in deltas_summary:
        prompt += f"""
### CHANGE #{d['index']}
- **ID**: `{d['delta_id']}`
- **Category**: {d['category']}
- **Location**: {d['locator_type']}: `{d['locator_value']}`
- **Old Value**: `{d['old_value']}`
- **New Value**: `{d['new_value']}`
- **Policy Tag**: {d['policy_tag']}

"""

    # Add output format specification - EXACT MATCH
    prompt += f"""
## OUTPUT FORMAT

Return ONLY valid JSON with this EXACT structure. Include drift_category for each item.

```json
{{
  "high": [
    {{
      "id": "delta_id_from_above",
      "file": "{file}",
      "locator": {{
        "type": "keypath",
        "value": "full.path.to.key"
      }},
      "old": "exact text that was removed or changed FROM",
      "new": "exact text that was added or changed TO",
      "drift_category": "Database|Network|Functional|Logical|Dependency|Configuration|Other",
      "why": "What changed and its impact",
      "ai_review_assistant": {{
        "potential_risk": "Specific risk and consequences (e.g., 'Service outage if database connection fails. Production users will see errors.')",
        "suggested_action": "Concrete steps to take (e.g., 'Verify credentials with DBA team. Test connection in staging. Deploy during maintenance window.')"
      }},
      "remediation": {{
        "snippet": "corrected configuration value"
      }}
    }}
  ],
  "medium": [
    {{
      "id": "delta_id_from_above",
      "file": "{file}",
      "locator": {{
        "type": "keypath",
        "value": "full.path.to.key"
      }},
      "old": "text before change",
      "new": "text after change",
      "drift_category": "Database|Network|Functional|Logical|Dependency|Configuration|Other",
      "why": "What changed and why it matters",
      "ai_review_assistant": {{
        "potential_risk": "Specific risk (e.g., 'Performance degradation during high load. Response time may increase by 20%.')",
        "suggested_action": "Concrete steps (e.g., 'Monitor response times. Load test in staging. Review with performance team.')"
      }},
      "remediation": {{
        "snippet": "corrected value"
      }}
    }}
  ],
  "low": [],
  "allowed_variance": [
    {{
      "id": "delta_id_from_above",
      "file": "{file}",
      "locator": {{
        "type": "keypath",
        "value": "full.path.to.key"
      }},
      "old": "text before change",
      "new": "text after change",
      "drift_category": "Database|Network|Functional|Logical|Dependency|Configuration|Other",
      "rationale": "Why this change is acceptable"
    }}
  ]
}}
```

## CRITICAL FIELD REQUIREMENTS

### For **high**, **medium**, **low** items:
- **id**: Use exact delta ID from above
- **file**: Use "{file}"
- **locator**: Copy the exact locator structure from the delta
  - **type**: keypath, yamlpath, jsonpath, unidiff, coord, or path
  - **value**: Full path to the configuration key
  - **If type is "unidiff"**: Also include old_start, old_lines, new_start, new_lines from the delta
- **old**: EXACT text that was removed/changed FROM (from Old Value above)
- **new**: EXACT text that was added/changed TO (from New Value above)
- **drift_category**: REQUIRED - Classify as one of: Database, Network, Functional, Logical, Dependency, Configuration, Other
- **why**: Single sentence explaining what changed and its impact
- **ai_review_assistant**: REQUIRED - Object with TWO fields:
  - **potential_risk**: Specific risk and consequences (e.g., "Service outage if connection fails. Users will see 500 errors.")
  - **suggested_action**: Concrete actionable steps (e.g., "Verify with DBA. Test in staging. Deploy during maintenance window.")
- **remediation**: Object with "snippet" field containing corrected value

### For **allowed_variance** items:
- **id**: Use exact delta ID from above
- **file**: Use "{file}"
- **locator**: Same as above
- **old**: EXACT text before change
- **new**: EXACT text after change
- **drift_category**: REQUIRED - Same classification as above
- **rationale**: Single sentence explaining why this variance is acceptable

## DRIFT CATEGORY GUIDELINES

Choose the most appropriate category:
- **Database**: Database connections, credentials, schemas, queries
- **Network**: URLs, endpoints, ports, hosts, IP addresses
- **Functional**: Feature flags, business logic, workflows
- **Logical**: Conditionals, algorithms, calculations
- **Dependency**: Libraries, packages, versions
- **Configuration**: General settings, timeouts, limits
- **Other**: Anything that doesn't fit above categories

## AI REVIEW ASSISTANT GUIDELINES

The `ai_review_assistant` field is CRITICAL for user decision-making. Be specific and actionable:

### **potential_risk** - Answer "What could go wrong?"
- ✅ GOOD: "Database connection will fail causing 500 errors. Users cannot complete orders. Revenue impact during peak hours."
- ❌ BAD: "Configuration changed" (too generic)
- ✅ GOOD: "Timeout too short may cause request failures under load. 10% of requests may fail during peak traffic."
- ❌ BAD: "Performance impact" (not specific)

### **suggested_action** - Answer "What should I do?"
- ✅ GOOD: "1. Verify credentials with DBA team. 2. Test connection in staging. 3. Deploy during maintenance window. 4. Monitor error rates."
- ❌ BAD: "Review the change" (not actionable)
- ✅ GOOD: "Revert timeout to 30s. Load test in staging with production traffic levels. If acceptable, document reason for change."
- ❌ BAD: "Check configuration" (too vague)

**Remember:** Users rely on this to make approve/reject decisions. Be specific, concrete, and actionable!

## DO NOT INCLUDE

DO NOT add these fields (they are NOT in the desired format):
- risk_level (inferred from bucket)
- risk_reason (use "why" instead)
- why_allowed (use "rationale" instead)
- remediation.steps (optional, can add if helpful)
- remediation.patch_hint (optional, only if you have full git diff)

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

## ANALYSIS INSTRUCTIONS

1. **Analyze each delta** from the list above
2. **Categorize into ONE bucket**: high, medium, low, or allowed_variance
3. **Use exact delta IDs** from above
4. **Keep locator structure** from the delta (especially for unidiff types)
5. **Write clear "why"** explaining what changed
6. **Write specific "ai_review_assistant"** with concrete risks and actions
7. **Provide remediation snippet** for high/medium/low items
8. **Return ONLY JSON** - no markdown, no explanations, just the JSON object

**CRITICAL:** Every high/medium/low item MUST have `ai_review_assistant` with both `potential_risk` and `suggested_action` fields!

Begin analysis now.
"""
    
    return prompt


def validate_llm_output(output: dict) -> bool:
    """
    Validate LLM output matches the EXACT format from LLM_output.json.
    
    Args:
        output: Parsed JSON output from AI
    
    Returns:
        True if valid, False otherwise
    """
    # Check top-level structure
    required_keys = ["high", "medium", "low", "allowed_variance"]
    if not all(key in output for key in required_keys):
        return False
    
    # Check each bucket is a list
    for key in required_keys:
        if not isinstance(output[key], list):
            return False
    
    # Check items have required fields (minimal set)
    for bucket in ["high", "medium", "low"]:
        for item in output[bucket]:
            if not isinstance(item, dict):
                return False
            
            # Required fields for high/medium/low (now includes old/new and ai_review_assistant)
            if not all(field in item for field in ["id", "file", "locator", "old", "new", "why", "ai_review_assistant", "remediation"]):
                return False
            
            # locator must have type and value
            if not isinstance(item["locator"], dict):
                return False
            if "type" not in item["locator"] or "value" not in item["locator"]:
                return False
            
            # ai_review_assistant must have potential_risk and suggested_action
            if not isinstance(item["ai_review_assistant"], dict):
                return False
            if "potential_risk" not in item["ai_review_assistant"] or "suggested_action" not in item["ai_review_assistant"]:
                return False
            
            # remediation must have snippet
            if not isinstance(item["remediation"], dict):
                return False
            if "snippet" not in item["remediation"]:
                return False
    
    # Check allowed_variance items
    for item in output["allowed_variance"]:
        if not isinstance(item, dict):
            return False
        
        # Required fields for allowed_variance (now includes old/new)
        if not all(field in item for field in ["id", "file", "locator", "old", "new", "rationale"]):
            return False
        
        # locator must have type and value
        if not isinstance(item["locator"], dict):
            return False
        if "type" not in item["locator"] or "value" not in item["locator"]:
            return False
    
    return True


def get_drift_categories() -> List[str]:
    """
    Return standard drift categories (for reference, not in output).
    """
    return [
        "Database",
        "Network",
        "Functional",
        "Logical",
        "Dependency",
        "Configuration",
        "Other"
    ]


def get_risk_levels() -> List[str]:
    """
    Return standard risk levels (for reference, not in output).
    """
    return ["high", "medium", "low"]

