// =============================================================================
// API DE SALUD DEL SISTEMA (CIRCUIT BREAKERS)
// =============================================================================

export type CircuitState = "CLOSED" | "OPEN" | "HALF_OPEN";

export interface CircuitBreakerStatus {
  name: string;
  state: CircuitState;
  failureCount: number;
  lastFailureTime?: string;
  recoveryTimeout?: number; // segundos
}

export interface SystemHealthStatus {
  status: "healthy" | "degraded" | "unhealthy";
  timestamp: string;
  circuits: Record<string, CircuitBreakerStatus>;
  version: string;
  uptime: number; // segundos
}

/**
 * Obtiene el status de salud del sistema con información de circuit breakers
 * Se integra con el endpoint /health del backend que implementa resiliencia
 */
export async function fetchSystemHealth(): Promise<SystemHealthStatus> {
  // Ajustar URL según tu configuración de API
  const response = await fetch("/api/v1/health", {
    headers: {
      "Accept": "application/json",
      // Agregar token si el endpoint requiere auth
      // "Authorization": `Bearer ${getToken()}`,
    },
    // Cache corto para status dinámico
    next: { revalidate: 10 }, // Next.js App Router: revalidar cada 10s
  });
  
  if (!response.ok) {
    throw new Error(`Health check failed: ${response.status}`);
  }
  
  return response.json();
}

/**
 * Hook para obtener el status de salud con polling automático
 */
export function useSystemHealth(refreshInterval: number = 30000) {
  return {
    queryKey: ["system-health"],
    queryFn: fetchSystemHealth,
    refetchInterval: refreshInterval,
    refetchOnWindowFocus: true,
    staleTime: 15000, // Considerar datos obsoletos después de 15s
  };
}

/**
 * Utilidad para determinar si un servicio específico está operativo
 */
export function isServiceOperational(
  health: SystemHealthStatus | undefined,
  serviceName: string
): boolean {
  if (!health) return false;
  
  const circuit = health.circuits[serviceName];
  if (!circuit) return true; // Si no hay circuito, asumir operativo
  
  return circuit.state === "CLOSED";
}

/**
 * Utilidad para obtener servicios con problemas
 */
export function getFailingServices(health: SystemHealthStatus | undefined): string[] {
  if (!health) return [];
  
  return Object.entries(health.circuits)
    .filter(([_, circuit]) => circuit.state !== "CLOSED")
    .map(([name]) => name);
}
