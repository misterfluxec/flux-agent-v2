import { useEffect } from 'react';
import { useEventBus, EventBusMessage } from '@/providers/EventBusProvider';
import { toast } from 'sonner';

export function CriticalEventToaster() {
  const { subscribe } = useEventBus();

  useEffect(() => {
    const unsubscribe = subscribe(["*"], (msg: EventBusMessage) => {
      const severity = msg.data?.metadata?.severity || 'low';
      const summary = msg.data?.metadata?.summary || `Evento: ${msg.type}`;

      // Only toast for critical or high severity operational/commerce events
      if (severity === 'critical' || severity === 'high') {
        const isCritical = severity === 'critical';
        toast(summary, {
          description: `Severidad: ${severity.toUpperCase()} - ${new Date().toLocaleTimeString()}`,
          style: isCritical ? {
            background: 'rgba(239, 68, 68, 0.1)',
            borderColor: 'rgba(239, 68, 68, 0.3)',
            color: '#fca5a5'
          } : {
            background: 'rgba(245, 158, 11, 0.1)',
            borderColor: 'rgba(245, 158, 11, 0.3)',
            color: '#fcd34d'
          },
          duration: isCritical ? 10000 : 5000,
        });
      }
    });

    return () => unsubscribe();
  }, [subscribe]);

  return null; // This is a logic-only component
}
