// =============================================================================
// FLUXAGENT V2 — ANALYTICS API CLIENT (CACHE-AWARE)
// =============================================================================
// Conexión con analytics_router_cached del backend
// Cache-aware para mejor performance
// =============================================================================

import { api } from '../api';

// =============================================================================
// TYPES
// =============================================================================

export interface AnalyticsOverview {
  total_conversations: number;
  total_messages: number;
  total_sales: number;
  conversion_rate: number;
  avg_response_time: number;
  sentiment_score: number;
  cache_status?: 'HIT' | 'MISS';
  cache_ttl?: number;
}

export interface DailyStats {
  date: string;
  conversations: number;
  messages: number;
  sales: number;
  leads: number;
}

export interface AgentStats {
  agent_id: string;
  agent_name: string;
  conversations: number;
  messages: number;
  leads: number;
  sales: number;
  avg_response_time: number;
  satisfaction_score: number;
}

export interface SentimentAnalysis {
  data: {
    date: string;
    positive: number;
    negative: number;
    neutral: number;
    overall_score: number;
  }[];
  summary: {
    overall_avg: number;
    total_conversations: number;
    granularity: string;
    period_days: number;
  };
}

export interface TopPerformingAgent {
  agent_id: string;
  agent_name: string;
  score: number;
  conversations: number;
  sales: number;
  satisfaction: number;
}

export interface AnalyticsFilters {
  days?: number;
  start_date?: string;
  end_date?: string;
  agent_id?: string;
  channel?: string;
  granularity?: 'hourly' | 'daily' | 'weekly';
  format?: string;
}

// =============================================================================
// API FUNCTIONS
// =============================================================================

/**
 * Obtiene el overview de analytics con cache-aware
 */
export async function fetchAnalyticsOverview(filters?: AnalyticsFilters): Promise<AnalyticsOverview> {
  const params = new URLSearchParams();
  
  if (filters?.days) params.append('days', filters.days.toString());
  if (filters?.start_date) params.append('start_date', filters.start_date);
  if (filters?.end_date) params.append('end_date', filters.end_date);
  if (filters?.agent_id) params.append('agent_id', filters.agent_id);
  if (filters?.channel) params.append('channel', filters.channel);

  const url = params.toString() ? `/analytics/overview?${params}` : '/analytics/overview';
  
  const { data, headers } = await api.get<AnalyticsOverview>(url);
  
  // Agregar metadata de cache si está disponible
  return {
    ...data,
    cache_status: headers['x-cache-status'] as 'HIT' | 'MISS' | undefined,
    cache_ttl: headers['x-cache-ttl'] ? parseInt(headers['x-cache-ttl']) : undefined
  };
}

/**
 * Obtiene estadísticas diarias con cache
 */
export async function fetchDailyStats(filters?: AnalyticsFilters): Promise<DailyStats[]> {
  const params = new URLSearchParams();
  
  if (filters?.days) params.append('days', filters.days.toString());
  if (filters?.start_date) params.append('start_date', filters.start_date);
  if (filters?.end_date) params.append('end_date', filters.end_date);
  if (filters?.agent_id) params.append('agent_id', filters.agent_id);
  if (filters?.granularity) params.append('granularity', filters.granularity);

  const url = params.toString() ? `/analytics/daily-stats?${params}` : '/analytics/daily-stats';
  
  const { data } = await api.get<DailyStats[]>(url);
  return data;
}

/**
 * Obtiene estadísticas por agente
 */
export async function fetchAgentStats(filters?: AnalyticsFilters): Promise<AgentStats[]> {
  const params = new URLSearchParams();
  
  if (filters?.days) params.append('days', filters.days.toString());
  if (filters?.start_date) params.append('start_date', filters.start_date);
  if (filters?.end_date) params.append('end_date', filters.end_date);

  const url = params.toString() ? `/analytics/agent-stats?${params}` : '/analytics/agent-stats';
  
  const { data } = await api.get<AgentStats[]>(url);
  return data;
}

/**
 * Obtiene análisis de sentimiento
 */
export async function fetchSentimentAnalysis(filters?: AnalyticsFilters): Promise<SentimentAnalysis> {
  const params = new URLSearchParams();
  
  if (filters?.days) params.append('days', filters.days.toString());
  if (filters?.start_date) params.append('start_date', filters.start_date);
  if (filters?.end_date) params.append('end_date', filters.end_date);
  if (filters?.granularity) params.append('granularity', filters.granularity || 'daily');

  const url = params.toString() ? `/analytics/sentiment-analysis?${params}` : '/analytics/sentiment-analysis';
  
  const { data } = await api.get<SentimentAnalysis>(url);
  return data;
}

/**
 * Obtiene top agentes performantes
 */
export async function fetchTopAgents(filters?: AnalyticsFilters): Promise<TopPerformingAgent[]> {
  const params = new URLSearchParams();
  
  if (filters?.days) params.append('days', filters.days.toString());
  if (filters?.start_date) params.append('start_date', filters.start_date);
  if (filters?.end_date) params.append('end_date', filters.end_date);

  const url = params.toString() ? `/analytics/top-agents?${params}` : '/analytics/top-agents';
  
  const { data } = await api.get<TopPerformingAgent[]>(url);
  return data;
}

/**
 * Invalida cache de analytics manualmente
 */
export async function invalidateAnalyticsCache(): Promise<{ message: string }> {
  const { data } = await api.post<{ message: string }>('/analytics/invalidate-cache');
  return data;
}

/**
 * Obtiene métricas de cache
 */
export async function fetchCacheMetrics(): Promise<{
  hit_rate: number;
  total_requests: number;
  cache_hits: number;
  cache_misses: number;
  avg_response_time: number;
}> {
  const { data } = await api.get('/analytics/cache-metrics');
  return data;
}

/**
 * Exporta datos de analytics a CSV
 */
export async function exportAnalyticsData(filters?: AnalyticsFilters): Promise<Blob> {
  const params = new URLSearchParams();
  
  if (filters?.days) params.append('days', filters.days.toString());
  if (filters?.start_date) params.append('start_date', filters.start_date);
  if (filters?.end_date) params.append('end_date', filters.end_date);
  if (filters?.agent_id) params.append('agent_id', filters.agent_id);
  if (filters?.format) params.append('format', 'csv');

  const url = params.toString() ? `/analytics/export?${params}` : '/analytics/export';
  
  const response = await api.get(url, {
    responseType: 'blob'
  });
  
  return response.data;
}

/**
 * Obtiene métricas en tiempo real (si está disponible)
 */
export async function fetchRealtimeMetrics(): Promise<{
  active_conversations: number;
  messages_per_minute: number;
  avg_response_time_last_hour: number;
  active_agents: number;
}> {
  const { data } = await api.get('/analytics/realtime');
  return data;
}

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

/**
 * Formatea número para display
 */
export function formatNumber(num: number): string {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M';
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K';
  }
  return num.toString();
}

/**
 * Formatea porcentaje
 */
export function formatPercentage(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

/**
 * Formatea tiempo en segundos a formato legible
 */
export function formatDuration(seconds: number): string {
  if (seconds < 60) {
    return `${seconds.toFixed(1)}s`;
  } else if (seconds < 3600) {
    return `${(seconds / 60).toFixed(1)}m`;
  } else {
    return `${(seconds / 3600).toFixed(1)}h`;
  }
}

/**
 * Calcula tendencia entre dos valores
 */
export function calculateTrend(current: number, previous: number): {
  value: number;
  percentage: number;
  direction: 'up' | 'down' | 'neutral';
} {
  if (previous === 0) {
    return {
      value: current,
      percentage: 100,
      direction: current > 0 ? 'up' : 'neutral'
    };
  }

  const percentage = ((current - previous) / previous) * 100;
  
  return {
    value: current - previous,
    percentage: Math.abs(percentage),
    direction: percentage > 0 ? 'up' : percentage < 0 ? 'down' : 'neutral'
  };
}
