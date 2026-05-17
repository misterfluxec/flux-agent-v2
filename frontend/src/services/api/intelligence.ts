import { apiClient } from '@/lib/api-client';

// Tipos para el Copilot (luego migrar a OpenAPI auto-generated)
export interface CopilotInsight {
  id: string;
  type: 'recommendation' | 'alert' | 'prediction' | 'explanation';
  priority: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  description: string;
  actionable: boolean;
  action_label?: string;
  action_endpoint?: string;
  metadata?: Record<string, any>;
  created_at?: string;
}

export interface ExplainabilityRequest {
  context: 'lead' | 'quote' | 'order' | 'payment' | 'inventory';
  entity_id: string;
}

export interface ExplainabilityResponse {
  signals: string[];
  policy_applied: string;
  confidence_pct: number;
  source: string;
  generated_at: string;
}

export interface AnomalyDetection {
  metric: string;
  expected_range: [number, number];
  actual_value: number;
  severity: 'low' | 'medium' | 'high';
  recommendation: string;
}

export interface MemorySummary {
  customer_id: string;
  episodic_count: number;
  semantic_profile: Record<string, any>;
  last_interaction: string;
  key_preferences: string[];
}

// === SERVICIOS DE INTELIGENCIA ===

export async function getInsights(params?: { limit?: number; priority?: string; type?: string }): Promise<CopilotInsight[]> {
  const qs = params ? `?${new URLSearchParams(params as any).toString()}` : '';
  const { data } = await apiClient.get<CopilotInsight[]>(`/copilot/insights${qs}`);
  return data;
}

export async function getInsight(id: string): Promise<CopilotInsight> {
  const { data } = await apiClient.get<CopilotInsight>(`/copilot/insights/${id}`);
  return data;
}

export async function acknowledgeInsight(id: string, action: 'accepted' | 'dismissed'): Promise<any> {
  const { data } = await apiClient.post(`/copilot/insights/${id}/acknowledge`, { action });
  return data;
}

export async function explainDecision(request: ExplainabilityRequest): Promise<ExplainabilityResponse> {
  const { data } = await apiClient.post<ExplainabilityResponse>('/copilot/explain', request);
  return data;
}

export async function getAnomalies(params?: { metric?: string; severity?: string; limit?: number }): Promise<AnomalyDetection[]> {
  const qs = params ? `?${new URLSearchParams(params as any).toString()}` : '';
  const { data } = await apiClient.get<AnomalyDetection[]>(`/copilot/anomalies${qs}`);
  return data;
}

export async function getCustomerMemory(customerId: string): Promise<MemorySummary> {
  const { data } = await apiClient.get<MemorySummary>(`/copilot/memory/customers/${customerId}`);
  return data;
}

export async function getNextBestAction(context: { customer_id?: string; order_id?: string; current_state: string }): Promise<CopilotInsight> {
  const { data } = await apiClient.post<CopilotInsight>('/copilot/next-action', context);
  return data;
}

export async function getDailyBriefing(): Promise<{ narrative: string; key_metrics: Record<string, any> }> {
  const { data } = await apiClient.get<{ narrative: string; key_metrics: Record<string, any> }>('/copilot/briefing/daily');
  return data;
}
