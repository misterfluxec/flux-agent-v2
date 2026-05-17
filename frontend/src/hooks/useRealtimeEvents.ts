"use client";

import { useEffect, useRef, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useEventBus, EventBusMessage } from '@/providers/EventBusProvider';

// Configuration
const DEDUPE_TTL_MS = 5 * 60 * 1000; // 5 minutos
const CLEANUP_INTERVAL_MS = 60 * 1000; // 1 minuto
const FALLBACK_POLLING_MS = 30 * 1000; // 30 segundos
const DEBOUNCE_MS = 500; // 500ms recomendado

export function useRealtimeEvents() {
  const { subscribe, isConnected } = useEventBus();
  const queryClient = useQueryClient();
  
  const processedEventsRef = useRef<Map<string, number>>(new Map());
  const debounceTimersRef = useRef<Map<string, NodeJS.Timeout>>(new Map());
  const lastEventReceivedAt = useRef<number>(Date.now());

  // Domain-partitioned debounce invalidation
  const debouncedInvalidate = useCallback((queryKey: string) => {
    if (debounceTimersRef.current.has(queryKey)) {
      clearTimeout(debounceTimersRef.current.get(queryKey)!);
    }
    const timer = setTimeout(() => {
      queryClient.invalidateQueries({ queryKey: [queryKey] });
      debounceTimersRef.current.delete(queryKey);
    }, DEBOUNCE_MS);
    debounceTimersRef.current.set(queryKey, timer);
  }, [queryClient]);

  // TTL Cleanup Interval
  useEffect(() => {
    const cleanupTimer = setInterval(() => {
      const now = Date.now();
      let deleted = 0;
      for (const [id, timestamp] of processedEventsRef.current.entries()) {
        if (now - timestamp > DEDUPE_TTL_MS) {
          processedEventsRef.current.delete(id);
          deleted++;
        }
      }
      if (deleted > 0) {
        console.debug(`[RealtimeEvents] Cleaned up ${deleted} stale dedupe entries.`);
      }
    }, CLEANUP_INTERVAL_MS);

    return () => clearInterval(cleanupTimer);
  }, []);

  // Visibility-aware fallback polling
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        const timeSinceLastEvent = Date.now() - lastEventReceivedAt.current;
        // Si el tab se vuelve visible y pasaron >30s sin eventos, asume status stale por si acaso
        if (timeSinceLastEvent > FALLBACK_POLLING_MS) {
          console.warn("[RealtimeEvents] Tab visible after idle + no recent events. Fallback polling triggered.");
          debouncedInvalidate('conversations');
          debouncedInvalidate('quotes');
          debouncedInvalidate('orders');
          lastEventReceivedAt.current = Date.now();
        }
      }
    };

    document.addEventListener("visibilitychange", handleVisibilityChange);
    return () => document.removeEventListener("visibilitychange", handleVisibilityChange);
  }, [debouncedInvalidate]);

  // Main Event Subscription
  useEffect(() => {
    const eventsToListen = [
      "quote.generated",
      "order.created",
      "message.received",
      "handoff.requested",
      "lead.hot"
    ];

    const unsubscribe = subscribe(eventsToListen, (msg: EventBusMessage) => {
      lastEventReceivedAt.current = Date.now();

      const eventId = msg.event_id || msg.id;
      if (eventId) {
        if (processedEventsRef.current.has(eventId)) {
          return; // Ignorar duplicado
        }
        processedEventsRef.current.set(eventId, Date.now());
      }

      console.log(`[RealtimeEvents] Received signal: ${msg.type}`, msg);

      switch (msg.type) {
        case "message.received":
        case "handoff.requested":
          debouncedInvalidate('conversations');
          break;
        case "quote.generated":
        case "order.created":
        case "lead.hot":
          debouncedInvalidate('conversations');
          debouncedInvalidate('quotes');
          debouncedInvalidate('orders');
          break;
        default:
          break;
      }
    });

    return () => {
      unsubscribe();
    };
  }, [subscribe, debouncedInvalidate]);
}
