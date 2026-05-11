import { useState, useEffect, useMemo } from 'react';
import { useInfiniteQuery, useQueryClient } from '@tanstack/react-query';
import { operations } from '@/services/api';
import { TimelineEvent, AggregateType } from '@/types/operations';
import { useEventBus, EventBusMessage } from '@/providers/EventBusProvider';

interface UseOperationsTimelineProps {
  aggregateType?: AggregateType;
  aggregateId?: string;
  limit?: number;
  realtime?: boolean;
}

export function useOperationsTimeline({
  aggregateType,
  aggregateId,
  limit = 20,
  realtime = true
}: UseOperationsTimelineProps) {
  const queryClient = useQueryClient();
  const { subscribe } = useEventBus();
  
  const SESSION_MUTATION_ID = useMemo(() => {
    if (typeof window !== 'undefined') {
      if (!(window as any).sessionMutationId) {
        (window as any).sessionMutationId = Math.random().toString(36).substring(7);
      }
      return (window as any).sessionMutationId;
    }
    return 'ssr';
  }, []);

  const [liveEvents, setLiveEvents] = useState<TimelineEvent[]>([]);
  const [pendingBurst, setPendingBurst] = useState<TimelineEvent[]>([]);

  const queryKey = aggregateType && aggregateId 
    ? ['timeline', aggregateType, aggregateId]
    : ['timeline', 'global'];

  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading,
    isError,
    error,
    refetch
  } = useInfiniteQuery({
    queryKey,
    queryFn: async ({ pageParam = 0 }) => {
      if (aggregateType && aggregateId) {
        return operations.getEntityTimeline(aggregateType, aggregateId, limit, pageParam as number);
      } else {
        return operations.getGlobalTimeline(undefined, undefined, limit, pageParam as number);
      }
    },
    getNextPageParam: (lastPage: any) => lastPage.has_more ? lastPage.next_cursor : undefined,
    initialPageParam: 0,
    staleTime: 1000 * 30, // 30 seconds
    gcTime: 1000 * 60 * 5, // 5 minutes
  });

  // Subscribe to live events via EventBus
  useEffect(() => {
    if (!realtime) return;

    const unsubscribe = subscribe(["*"], (msg: EventBusMessage) => {
      const payload = msg.data || {};
      const metadata = payload.metadata || {};
      
      if (aggregateType && aggregateId) {
        if (metadata.aggregate_type !== aggregateType || metadata.aggregate_id !== aggregateId) {
          return;
        }
      }

      if (metadata.mutation_source_id && metadata.mutation_source_id === SESSION_MUTATION_ID) {
        return; // Ignore echo
      }

      // 4.2 Compaction: Ignorar eventos ruidosos en la vista live (typing, delivery)
      if (['message.typing', 'message.delivery', 'system.ping'].includes(msg.type)) {
        return;
      }

      const newEvent: TimelineEvent = {
        id: metadata.event_id || msg.event_id || Date.now().toString(),
        type: msg.type,
        timestamp: metadata.timestamp || new Date().toISOString(),
        category: getCategoryForType(msg.type),
        severity: metadata.severity || 'low',
        summary: metadata.summary || `Evento: ${msg.type}`,
        payload: payload,
        priority_score: metadata.priority_score || 0,
        tags: metadata.tags || [],
        ack_state: 'unresolved',
        // Reconciliation fields
        updated_at: metadata.updated_at,
        updated_by: metadata.updated_by ? {
          id: metadata.updated_by.id,
          name: metadata.updated_by.name,
          type: metadata.updated_by.type
        } : undefined,
        mutation_source_id: metadata.mutation_source_id,
        version: metadata.version
      };

      setPendingBurst(prev => {
        if (prev.some(e => e.id === newEvent.id)) return prev;
        return [newEvent, ...prev];
      });
      
      
      // Invalidate to fetch canonical in background
      queryClient.invalidateQueries({ queryKey });
    });

    return () => unsubscribe();
  }, [realtime, aggregateType, aggregateId, subscribe, queryClient, queryKey, SESSION_MUTATION_ID]);

  // Burst auto-flush logic
  useEffect(() => {
    if (pendingBurst.length === 0) return;
    
    // If we have a massive burst, stop auto-flushing to let user click the pill
    if (pendingBurst.length >= 5) {
      return; 
    }

    // Auto flush small bursts after 500ms
    const timer = setTimeout(() => {
      setLiveEvents(prev => {
        const merged = [...pendingBurst, ...prev];
        // deduplicate just in case
        const seen = new Set();
        return merged.filter(e => {
          if (seen.has(e.id)) return false;
          seen.add(e.id);
          return true;
        }).slice(0, 50);
      });
      setPendingBurst([]);
    }, 500);

    return () => clearTimeout(timer);
  }, [pendingBurst]);

  const flushBurst = () => {
    setLiveEvents(prev => {
      const merged = [...pendingBurst, ...prev];
      const seen = new Set();
      return merged.filter(e => {
        if (seen.has(e.id)) return false;
        seen.add(e.id);
        return true;
      }).slice(0, 50);
    });
    setPendingBurst([]);
  };

  // Merge and deduplicate events
  const allEvents = useMemo(() => {
    const pagesEvents = data?.pages.flatMap(page => page.events || []) || [];
    const merged = [...liveEvents, ...pagesEvents];
    const seen = new Set<string>();
    
    return merged.filter(e => {
      if (!e || !e.id) return false;
      if (seen.has(e.id)) return false;
      seen.add(e.id);
      return true;
    }).sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
  }, [data, liveEvents]);

  // Group events by date and collapse consecutive same-type events
  const groupedEvents = useMemo(() => {
    const groups: Record<string, any[]> = {};
    
    // First group by consecutive types
    const collapsedEvents = [];
    let currentGroup = null;

    for (const event of allEvents) {
      if (!currentGroup) {
        currentGroup = { type: event.type, events: [event] };
      } else if (currentGroup.type === event.type && currentGroup.events.length < 5) {
        // Group consecutive of same type up to 5
        currentGroup.events.push(event);
      } else {
        collapsedEvents.push(currentGroup);
        currentGroup = { type: event.type, events: [event] };
      }
    }
    if (currentGroup) collapsedEvents.push(currentGroup);

    // Then group by date string
    collapsedEvents.forEach(group => {
      // Use the timestamp of the first event in the group
      const firstEvent = group.events[0];
      const date = new Date(firstEvent.timestamp).toLocaleDateString('es-ES', { 
        day: '2-digit', month: 'short', year: 'numeric' 
      });
      if (!groups[date]) groups[date] = [];
      groups[date].push(group);
    });
    return groups;
  }, [allEvents]);

  return {
    events: allEvents,
    groupedEvents,
    isLoading,
    isError,
    error,
    refetch,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    liveEventsCount: liveEvents.length,
    pendingBurstCount: pendingBurst.length >= 5 ? pendingBurst.length : 0,
    flushBurst
  };
}

function getCategoryForType(type: string): 'interaction' | 'commerce' | 'ops' | 'automation' | 'system' | 'billing' {
  if (type.startsWith('message.') || type.startsWith('conversation.')) return 'interaction';
  if (type.startsWith('quote.') || type.startsWith('order.') || type.startsWith('payment.') || type.startsWith('booking.') || type.startsWith('lead.')) return 'commerce';
  if (type.startsWith('handoff.') || type.startsWith('alert.')) return 'ops';
  if (type.startsWith('followup.') || type.startsWith('tool.')) return 'automation';
  if (type.startsWith('billing.') || type.startsWith('tenant.')) return 'billing';
  return 'system';
}
