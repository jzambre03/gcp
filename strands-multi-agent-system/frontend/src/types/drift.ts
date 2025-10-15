export interface DriftLocator {
  type: string;
  value: string;
  line_start?: number;
  line_end?: number;
  old_start?: number;
  old_lines?: number;
  new_start?: number;
  new_lines?: number;
}

export interface AIReviewAssistant {
  potential_risk: string;
  suggested_action: string;
}

export interface Remediation {
  snippet: string;
  steps?: string[];
  patch_hint?: string;
}

export interface DriftItem {
  id: string;
  file: string;
  locator: DriftLocator;
  old: string | null;
  new: string | null;
  drift_category?: string;
  why?: string;
  ai_review_assistant?: AIReviewAssistant;
  remediation?: Remediation;
  rationale?: string; // For allowed_variance items
}

export interface DriftSummary {
  total_config_files: number;
  files_with_drift: number;
  total_drifts: number;
  high_risk: number;
  medium_risk: number;
  low_risk: number;
  allowed_variance: number;
}

export interface LLMOutput {
  summary: DriftSummary;
  high: DriftItem[];
  medium: DriftItem[];
  low: DriftItem[];
  allowed_variance: DriftItem[];
}

export type RiskLevel = 'high' | 'medium' | 'low' | 'allowed';


