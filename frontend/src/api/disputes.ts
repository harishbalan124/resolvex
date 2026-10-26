import { apiClient } from './client';
import { Dispute, DisputeScanResult } from '../types/dispute';

export async function fetchDisputes(params?: { status?: string; rule?: string; limit?: number }): Promise<Dispute[]> {
  const response = await apiClient.get<Dispute[]>('/disputes', { params });
  return response.data;
}

export async function triggerBatchScanApi(limit: number = 100): Promise<DisputeScanResult> {
  const response = await apiClient.post<DisputeScanResult>('/disputes/scan-batch', null, {
    params: { limit },
  });
  return response.data;
}
