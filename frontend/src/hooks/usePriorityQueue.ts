import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { operations } from '@/services/api';
import { AckState } from '@/types/operations';

export function usePriorityQueue(limit: number = 20, tags?: string) {
  const queryClient = useQueryClient();
  const queryKey = ['operations', 'priority-queue', limit, tags];

  const { data: queue, isLoading, isError, refetch } = useQuery({
    queryKey,
    queryFn: () => operations.getPriorityQueue(limit, tags),
    staleTime: 1000 * 30, // 30s stale time
  });

  // Acciones comunes para la UI del queue
  const acknowledgeMutation = useMutation({
    mutationFn: (variables: { eventId: string, state: AckState, snooze_minutes?: number }) => {
      return operations.acknowledgeEvent(variables.eventId, { 
        state: variables.state, 
        snooze_minutes: variables.snooze_minutes 
      });
    },
    onSuccess: () => {
      // Invalida la cola para que se recargue
      queryClient.invalidateQueries({ queryKey });
    }
  });

  const assignMutation = useMutation({
    mutationFn: (variables: { eventId: string, assigned_to?: string, assigned_team?: string }) => {
      return operations.assignEvent(variables.eventId, {
        assigned_to: variables.assigned_to,
        assigned_team: variables.assigned_team
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey });
    }
  });

  return {
    queue,
    isLoading,
    isError,
    refetch,
    acknowledgeEvent: acknowledgeMutation.mutateAsync,
    assignEvent: assignMutation.mutateAsync,
    isMutating: acknowledgeMutation.isPending || assignMutation.isPending
  };
}
