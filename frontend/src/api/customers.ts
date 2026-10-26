import { apiClient } from './client';
import { Customer, CustomerDetail } from '../types/customer';

export async function fetchCustomers(params?: { tier?: string; search?: string; limit?: number; skip?: number }): Promise<Customer[]> {
  const response = await apiClient.get<Customer[]>('/customers', { params });
  return response.data;
}

export async function fetchCustomerDetail(customerId: number): Promise<CustomerDetail> {
  const response = await apiClient.get<CustomerDetail>(`/customers/${customerId}`);
  return response.data;
}

export async function createCustomerApi(data: Partial<Customer>): Promise<Customer> {
  const response = await apiClient.post<Customer>('/customers', data);
  return response.data;
}
