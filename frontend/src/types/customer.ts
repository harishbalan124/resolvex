export interface Customer {
  id: number;
  external_id: string;
  name: string;
  email: string;
  phone?: string | null;
  tier: string;
  churn_risk_score?: number | null;
  sentiment_score?: number | null;
  created_at: string;
  updated_at: string;
}

export interface CustomerDetail extends Customer {
  transactions_count: number;
  interactions_count: number;
  complaints_count: number;
  disputes_count: number;
}
