export interface Service {
  id: string;
  name: string;
  description?: string;
  repo_url: string;
  golden_branch: string;
  drift_branch: string;
  environment: 'production' | 'staging' | 'qa' | 'dev';
  status?: 'healthy' | 'warning' | 'error' | 'unknown';
  last_analysis?: string;
  drift_count?: number;
  high_risk?: number;
}

export interface ServiceConfig {
  name: string;
  repo_url: string;
  golden_branch: string;
  drift_branch: string;
  environment: string;
}


