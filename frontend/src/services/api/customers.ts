import { apiClient } from '@/lib/api-client';

export interface CustomerMetrics {
  ltv: number;
  order_count: number;
  churn_score: number;
  health_state: string;
  last_purchase_at?: string;
}

export interface CustomerMaster {
  id: string;
  name: string;
  email?: string;
  phone?: string;
  lifecycle_stage: string;
  metrics: CustomerMetrics;
}

export interface CustomerPreferences {
  transactional_consent: boolean;
  marketing_automation_consent: boolean;
  global_opt_out: boolean;
}

export interface Customer360Profile extends CustomerMaster {
  first_name?: string;
  last_name?: string;
  preferences: CustomerPreferences;
}

export interface CustomerTimelineEvent {
  id: string;
  type: string;
  timestamp: string;
  source: {
    type: string;
    id: string;
  };
  payload: any;
  visibility: string;
  importance: number;
}

export const customersApi = {
  getCustomers: async (): Promise<CustomerMaster[]> => {
    const { data } = await apiClient.get('/api/v1/customers');
    return data;
  },
  
  getCustomer360: async (id: string): Promise<Customer360Profile> => {
    const { data } = await apiClient.get(`/api/v1/customers/${id}`);
    return data;
  },
  
  getCustomerTimeline: async (id: string): Promise<{events: CustomerTimelineEvent[]}> => {
    const { data } = await apiClient.get(`/api/v1/customers/${id}/timeline`);
    return data;
  }
};
