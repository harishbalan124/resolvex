import { apiClient } from './client';
import { Complaint } from '../types/complaint';

export async function fetchComplaints(params?: { status?: string; assigned_to_me?: boolean; limit?: number }): Promise<Complaint[]> {
  const response = await apiClient.get<Complaint[]>('/complaints', { params });
  return response.data;
}

export async function fetchComplaintDetail(id: number): Promise<Complaint> {
  const response = await apiClient.get<Complaint>(`/complaints/${id}`);
  return response.data;
}

export async function createComplaintApi(payload: { customer_id: number; title: string; description: string; category: string; priority: string }): Promise<Complaint> {
  const response = await apiClient.post<Complaint>('/complaints', payload);
  return response.data;
}

export async function updateComplaintStatusApi(id: number, status: string, comment?: string): Promise<Complaint> {
  const response = await apiClient.patch<Complaint>(`/complaints/${id}/status`, { status, comment });
  return response.data;
}
