import { useQuery } from '@tanstack/react-query';
import { operations } from '@/services/api';

export function useOperationsHealth(pollingIntervalMs: number = 30000) {
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['operations', 'health'],
    queryFn: () => operations.getOperationalHealth(),
    refetchInterval: pollingIntervalMs, // Default 30s polling for health stats
    staleTime: 1000 * 15,
  });

  return {
    report: data,
    isLoading,
    isError,
    error,
    refetch
  };
}
