import { apiClient } from './client';
import { ChurnPrediction, EngineStatus, SentimentPrediction } from '../types/analytics';

export async function fetchEngineStatus(): Promise<EngineStatus> {
  const response = await apiClient.get<EngineStatus>('/analytics/status');
  return response.data;
}

export async function predictSentimentApi(text: string): Promise<SentimentPrediction> {
  const response = await apiClient.post<SentimentPrediction>('/analytics/sentiment', { text });
  return response.data;
}

export async function evaluateCustomerChurnApi(customerId: number): Promise<ChurnPrediction> {
  const response = await apiClient.post<ChurnPrediction>(`/analytics/churn/customer/${customerId}`);
  return response.data;
}
