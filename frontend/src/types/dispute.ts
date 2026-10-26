export interface Dispute {
  id: number;
  dispute_reference: string;
  transaction_id: number;
  customer_id: number;
  complaint_id?: number | null;
  reason: string;
  status: 'DETECTED' | 'UNDER_REVIEW' | 'ACTION_RECOMMENDED' | 'RESOLVED_APPROVED' | 'RESOLVED_REJECTED';
  rule_triggered: string;
  risk_score: number;
  created_at: string;
  updated_at: string;
}

export interface DisputeScanResult {
  scanned_count: number;
  disputes_detected: number;
  dispute_ids: number[];
}
