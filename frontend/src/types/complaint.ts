export interface ComplaintStatusHistory {
  id: number;
  complaint_id: number;
  changed_by_user_id?: number | null;
  old_status?: string | null;
  new_status: string;
  comment?: string | null;
  created_at: string;
}

export interface Complaint {
  id: number;
  ticket_number: string;
  customer_id: number;
  assigned_user_id?: number | null;
  title: string;
  description: string;
  category: string;
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  status: 'OPEN' | 'IN_INVESTIGATION' | 'PENDING_APPROVAL' | 'RESOLVED' | 'CLOSED';
  sla_deadline?: string | null;
  created_at: string;
  updated_at: string;
  status_history?: ComplaintStatusHistory[];
}
