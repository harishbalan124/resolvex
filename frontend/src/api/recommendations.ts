import { apiClient } from './client';
import { Recommendation, ReviewActionPayload } from '../types/recommendation';

export async function fetchRecommendations(params?: { status?: string; limit?: number }): Promise<Recommendation[]> {
  const response = await apiClient.get<Recommendation[]>('/recommendations', { params });
  return response.data;
}

export async function reviewRecommendationApi(id: number, payload: ReviewActionPayload): Promise<Recommendation> {
  const response = await apiClient.post<Recommendation>(`/recommendations/${id}/review`, payload);
  return response.data;
}

export async function generateRecommendationApi(disputeId: number): Promise<Recommendation> {
  const response = await apiClient.post<Recommendation>(`/recommendations/generate-for-dispute/${disputeId}`);
  return response.data;
}
