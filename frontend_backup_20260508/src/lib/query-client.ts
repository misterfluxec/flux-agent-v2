// =============================================================================
// FLUXAGENT V2 — QUERY CLIENT CONFIGURATION
// =============================================================================
// Configuración centralizada de React Query con cache sincronizado
// Sincronización con TTL del backend (60s)
// =============================================================================

import { QueryClient, keepPreviousData } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // 🔑 CLAVE: staleTime = TTL del backend (60s)
      staleTime: 60_000,
      gcTime: 5 * 60_000, // Mantener en caché 5 min si no se usa
      refetchOnWindowFocus: false,
      retry: (failureCount, error: any) => {
        // No reintentar si es rate limit (429) o error de auth (401)
        if ([401, 403, 429].includes(error?.status)) return false;
        return failureCount < 2;
      },
      // Placeholder data para UX fluida
      placeholderData: keepPreviousData,
    },
    mutations: {
      // Invalidar cache de analytics tras crear/editar agente
      onSuccess: (_data, _vars, context: any) => {
        if (context?.invalidates?.includes('analytics')) {
          queryClient.invalidateQueries({ queryKey: ['analytics'] });
        }
      }
    }
  }
});

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

/**
 * Invalida todas las queries de analytics
 */
export function invalidateAnalyticsQueries() {
  queryClient.invalidateQueries({ queryKey: ['analytics'] });
}

/**
 * Invalida queries específicas de agentes
 */
export function invalidateAgentQueries() {
  queryClient.invalidateQueries({ queryKey: ['agents'] });
  // También invalidar analytics ya que afecta las métricas
  queryClient.invalidateQueries({ queryKey: ['analytics'] });
}

/**
 * Invalida queries de conversaciones
 */
export function invalidateConversationQueries() {
  queryClient.invalidateQueries({ queryKey: ['conversations'] });
}

/**
 * Prefetch datos para mejor UX
 */
export function prefetchAnalyticsData(days: number = 7) {
  queryClient.prefetchQuery({
    queryKey: ['analytics-overview', days],
    queryFn: () => import('./api/analytics').then(m => m.fetchAnalyticsOverview({ days })),
    staleTime: 60_000
  });
}

/**
 * Configura contexto de mutación con invalidación automática
 */
export function createMutationConfig(invalidateKeys: string[] = []) {
  return {
    onSuccess: () => {
      invalidateKeys.forEach(key => {
        queryClient.invalidateQueries({ queryKey: [key] });
      });
    }
  };
}
