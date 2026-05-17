import { useQuery } from '@tanstack/react-query';
import { dashboardApi, DashboardKPIs } from '@/services/api/dashboard';

/**
 * Hook para obtener los datos reales del dashboard con React Query.
 * Maneja caché, refetching y estados de carga.
 */
export function useDashboardOverview() {
  return useQuery<DashboardKPIs>({
    queryKey: ['dashboard-overview'],
    queryFn: () => dashboardApi.getOverview(),
    refetchInterval: 60000, // Refrescar cada minuto
    staleTime: 30000,       // Considerar datos frescos por 30s
  });
}
