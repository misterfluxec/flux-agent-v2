import { apiClient } from "@/lib/api-client";

export interface HealthResponse {
  status: "saludable" | "degradado";
  servicios: Record<string, { status: string; latencia_ms?: number }>;
  version: string;
}

export interface StatsOverviewResponse {
  kpis: {
    total_conversaciones: number;
    leads_capturados: number;
    sentimiento_promedio: number;
    uso_tokens: number;
  };
  mensajes_por_dia: { fecha: string; conteo: number }[];
  sentimiento_distribucion: { name: string; value: number; fill: string }[];
  actividad_reciente: { id: string; action: string; agent: string; time: string; status: string }[];
}

export async function fetchHealth(): Promise<HealthResponse> {
  // We use the absolute path /health because it bypasses the /api/v1 prefix
  const { data } = await apiClient.get<HealthResponse>("/health");
  return data;
}

export async function fetchStatsOverview(): Promise<StatsOverviewResponse> {
  const { data } = await apiClient.get<StatsOverviewResponse>("/stats/overview");
  return data;
}
