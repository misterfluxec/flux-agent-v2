import { useEffect, useState } from 'react';
import { useEventBus } from '@/providers/EventBusProvider';
import type { EventBusMessage } from '@/providers/EventBusProvider';

const CRITICAL_EVENT_TYPES = [
  'LEAD_HOT',
  'HANDOFF_REQUESTED',
  'SYSTEM_ALERT',
  'QUOTA_EXCEEDED'
];

export function useCriticalEvents() {
  const { history } = useEventBus();
  const [criticalEvents, setCriticalEvents] = useState<EventBusMessage[]>([]);

  useEffect(() => {
    if (history.length === 0) return;
    
    const lastEvent = history[history.length - 1];
    if (CRITICAL_EVENT_TYPES.includes(lastEvent.type)) {
      setCriticalEvents(prev => {
        // Prevent duplicates
        if (prev.find(e => e.id === lastEvent.id)) return prev;
        return [lastEvent, ...prev].slice(0, 10); // Keep last 10 critical
      });
    }
  }, [history]);

  return { criticalEvents };
}
