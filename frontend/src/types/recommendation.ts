export interface Recommendation {
  id: number;
  dispute_id?: number | null;
  complaint_id?: number | null;
  suggested_action: string;
  justification: string;
  confidence_score: number;
  status: 'PENDING' | 'APPROVED' | 'REJECTED';
  reviewed_by_user_id?: number | null;
  review_notes?: string | null;
  reviewed_at?: string | null;
  created_at: string;
}

export interface ReviewActionPayload {
  action: 'APPROVED' | 'REJECTED';
  notes?: string;
}
