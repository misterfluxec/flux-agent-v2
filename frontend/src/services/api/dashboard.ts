/**
 * dashboard.ts — API Service para el Dashboard Principal (Control)
 * Conecta los KPIs y métricas con el backend real de FluxAgent V2
 */

import { apiClient } from "@/lib/api-client";

export interface DashboardKPIs {
  kpis: {
    total_conversaciones: number;
    leads_capturados: number;
    sentimiento_promedio: number;
    uso_tokens: number;
  };
  mensajes_por_dia: Array<{ fecha: string; conteo: number }>;
  sentimiento_distribucion: Array<{ name: string; value: number; fill: string }>;
  actividad_reciente: Array<{ 
    id: string; 
    action: string; 
    agent: string; 
    time: string; 
    status: string 
  }>;
}

export const dashboardApi = {
  /** Obtiene el resumen de KPIs y actividad del dashboard */
  getOverview: async (): Promise<DashboardKPIs> => {
    const response = await apiClient.get<DashboardKPIs>("/stats/overview");
    return response.data;
  },
};

export interface RecentActivity {
  id: string;
  type: "message" | "order" | "lead" | "payment" | "handoff" | "alert" | "channel_event";
  title: string;
  description: string;
  timestamp: string;
  urgency?: "low" | "medium" | "high" | "critical";
  action_url?: string;
  metadata?: Record<string, unknown>;
}

export interface TopMetrics {
  top_products: { name: string; units_sold: number; revenue: number }[];
  top_agents: { name: string; conversations: number; resolution_rate: number }[];
  channel_distribution: { channel: string; count: number; percentage: number }[];
  hourly_messages: { hour: string; count: number }[];
}

// ─── API Functions ──────────────────────────────────────────────────────────

/** KPIs principales del dashboard (se refresca cada 30s) */
export async function getDashboardOverview(): Promise<DashboardKPIs> {
  const res = await apiClient.get<DashboardKPIs>("/stats/overview");
  return res.data;
}

/** Feed de actividad reciente (últimos N eventos) */
export async function getRecentActivity(limit = 20): Promise<RecentActivity[]> {
  const res = await apiClient.get<RecentActivity[]>(`/stats/activity?limit=${limit}`);
  return res.data;
}

/** Métricas para gráficas (con caché de 5 min en backend) */
export async function getTopMetrics(
  period: "today" | "week" | "month" = "today"
): Promise<TopMetrics> {
  const res = await apiClient.get<TopMetrics>(`/analytics/overview?period=${period}`);
  return res.data;
}

/** Estado de salud del sistema */
export async function getSystemHealth(): Promise<{
  status: "healthy" | "degraded" | "down";
  services: { name: string; status: "up" | "down" | "degraded"; latency_ms?: number }[];
  uptime_pct: number;
}> {
  const res = await apiClient.get<{
    status: "healthy" | "degraded" | "down";
    services: { name: string; status: "up" | "down" | "degraded"; latency_ms?: number }[];
    uptime_pct: number;
  }>("/health/status");
  return res.data;
}
