import { apiClient } from './client';
import { AuditLog } from '../types/audit';

export async function fetchAuditLogs(params?: { action?: string; entity_type?: string; limit?: number }): Promise<AuditLog[]> {
  const response = await apiClient.get<AuditLog[]>('/audit-logs', { params });
  return response.data;
}
