export interface Transaction {
  id: number;
  customer_id: number;
  external_txn_id: string;
  amount: number | string;
  currency: string;
  merchant: string;
  category: string;
  txn_timestamp: string;
  status: 'COMPLETED' | 'PENDING' | 'FLAGGED' | 'DISPUTED' | 'REFUNDED';
  created_at: string;
}
