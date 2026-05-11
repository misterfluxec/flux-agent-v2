'use client';

import { useState, useMemo } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuTrigger,
  DropdownMenuSeparator,
  DropdownMenuLabel 
} from '@/components/ui/dropdown-menu';
import { TimelineEvent, ActionDefinition, AckRequest } from '@/types/operations';
import { operations } from '@/services/api';
import { toast } from 'sonner';

interface Props {
  event: TimelineEvent;
  onAction?: (action: string, event: TimelineEvent) => void;
}

const ACTION_DEFINITIONS: Record<string, ActionDefinition[]> = {
  'quote.generated': [
    { id: 'view_quote', label: 'Ver cotización', icon: '👁️', variant: 'primary', enabled: true },
    { id: 'send_payment_link', label: 'Enviar link de pago', icon: '💳', variant: 'secondary', enabled: false },
    { id: 'extend_validity', label: 'Extender validez', icon: '⏰', variant: 'secondary', enabled: false },
  ],
  'quote.accepted': [
    { id: 'create_order', label: 'Crear orden', icon: '📦', variant: 'primary', enabled: true },
    { id: 'send_confirmation', label: 'Enviar confirmación', icon: '✅', variant: 'secondary', enabled: false },
  ],
  'order.created': [
    { id: 'view_order', label: 'Ver orden', icon: '👁️', variant: 'primary', enabled: true },
    { id: 'send_payment_link', label: 'Enviar link de pago', icon: '💳', variant: 'primary', enabled: false },
    { id: 'escalate_to_human', label: 'Escalar a humano', icon: '👤', variant: 'warning', enabled: true },
  ],
  'order.paid': [
    { id: 'view_receipt', label: 'Ver comprobante', icon: '🧾', variant: 'secondary', enabled: true },
    { id: 'schedule_delivery', label: 'Programar entrega', icon: '🚚', variant: 'primary', enabled: false },
    { id: 'schedule_followup', label: 'Programar seguimiento', icon: '⏰', variant: 'secondary', enabled: false },
  ],
  'handoff.requested': [
    { id: 'take_control', label: 'Tomar control', icon: '👤', variant: 'primary', enabled: true },
    { id: 'assign_to_teammate', label: 'Asignar a compañero', icon: '👥', variant: 'secondary', enabled: true },
    { id: 'view_context', label: 'Ver contexto completo', icon: '📋', variant: 'secondary', enabled: true },
  ],
  'lead.hot': [
    { id: 'contact_now', label: 'Contactar ahora', icon: '📞', variant: 'primary', enabled: true },
    { id: 'create_quote', label: 'Crear cotización rápida', icon: '📄', variant: 'secondary', enabled: false },
    { id: 'assign_to_sales', label: 'Asignar a ventas', icon: '👔', variant: 'secondary', enabled: true },
  ],
};

const DEFAULT_ACTIONS: ActionDefinition[] = [
  { id: 'view_details', label: 'Ver detalles', icon: '🔍', variant: 'secondary', enabled: true },
  { id: 'acknowledge', label: 'Marcar Acknowledged', icon: '✓', variant: 'primary', enabled: true },
  { id: 'resolve', label: 'Marcar Resuelto', icon: '✅', variant: 'primary', enabled: true },
];

export function ActionMenu({ event, onAction }: Props) {
  const [open, setOpen] = useState(false);
  const queryClient = useQueryClient();
  
  const actions = useMemo(() => {
    // If it has a specific definition use it, plus standard ops actions
    const typeActions = ACTION_DEFINITIONS[event.type] || [];
    
    const combinedActions = [...typeActions];
    
    // Always provide fallback ops actions if unresolved
    if (event.ack_state === 'unresolved') {
      combinedActions.push({ id: 'acknowledge', label: 'Marcar Acknowledged', icon: '✓', variant: 'primary', enabled: true });
    }
    if (event.ack_state !== 'resolved') {
      combinedActions.push({ id: 'resolve', label: 'Marcar Resuelto', icon: '✅', variant: 'primary', enabled: true });
    }
    
    if (combinedActions.length === 0) {
      combinedActions.push(...DEFAULT_ACTIONS);
    }
    
    return combinedActions
      .filter(a => a.enabled)
      .map(a => ({
        ...a,
        tooltip: `${a.label} para ${event.summary.slice(0, 15)}...`
      }));
  }, [event]);

  // Optimistic ACK Mutation
  const ackMutation = useMutation({
    mutationFn: (data: AckRequest) => operations.acknowledgeEvent(event.id, data),
    onMutate: async (variables) => {
      await queryClient.cancelQueries({ queryKey: ['operations'] });
      await queryClient.cancelQueries({ queryKey: ['timeline'] });

      // Queue optimistic update
      const previousQueue = queryClient.getQueryData(['operations', 'priority-queue']);
      queryClient.setQueryData(['operations', 'priority-queue'], (old: any) => {
        if (!old) return old;
        // If resolved or acknowledged, we might want to keep it or remove it from queue
        // Typically queue is for unresolved/urgent. Let's filter out if resolved
        if (variables.state === 'resolved') {
          return old.filter((e: TimelineEvent) => e.id !== event.id);
        }
        return old.map((e: TimelineEvent) => e.id === event.id ? { ...e, ack_state: variables.state } : e);
      });

      return { previousQueue };
    },
    onError: (err, newTodo, context) => {
      queryClient.setQueryData(['operations', 'priority-queue'], context?.previousQueue);
      toast.error('No se pudo actualizar el estado del evento.');
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['operations'] });
      queryClient.invalidateQueries({ queryKey: ['timeline'] });
    },
  });

  const handleSelect = (actionId: string) => {
    setOpen(false);

    if (actionId === 'acknowledge') {
      ackMutation.mutate({ state: 'acknowledged' });
      return;
    }
    if (actionId === 'resolve') {
      ackMutation.mutate({ state: 'resolved' });
      return;
    }
    if (actionId === 'copy_event_id') {
      navigator.clipboard.writeText(event.id);
      toast.success('ID copiado al portapapeles');
      return;
    }

    if (onAction) {
      onAction(actionId, event);
    } else {
      toast.info(`Acción ${actionId} en desarrollo.`);
    }
  };

  const getVariantClasses = (variant: ActionDefinition['variant']) => {
    switch (variant) {
      case 'primary': return 'text-cyan-400 hover:text-cyan-300 hover:bg-cyan-500/10';
      case 'warning': return 'text-amber-400 hover:text-amber-300 hover:bg-amber-500/10';
      case 'danger': return 'text-red-400 hover:text-red-300 hover:bg-red-500/10';
      default: return 'text-slate-300 hover:text-slate-100 hover:bg-white/5';
    }
  };

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <DropdownMenuTrigger asChild>
        <button 
          className="p-1.5 rounded bg-white/5 hover:bg-white/10 border border-white/10 transition text-slate-400 hover:text-slate-200"
          title="Acciones rápidas"
        >
          ⚡
        </button>
      </DropdownMenuTrigger>
      
      <DropdownMenuContent 
        align="end" 
        className="w-56 bg-slate-900/95 backdrop-blur-md border border-white/10 shadow-2xl z-[100]"
        sideOffset={4}
      >
        <DropdownMenuLabel className="text-[10px] text-slate-500 font-normal px-2 py-1.5 truncate">
          Acciones: {event.type}
        </DropdownMenuLabel>
        <DropdownMenuSeparator className="bg-white/10" />
        
        {actions.map(action => (
          <DropdownMenuItem
            key={action.id}
            onClick={() => handleSelect(action.id)}
            className={`flex items-center gap-2 text-sm cursor-pointer ${getVariantClasses(action.variant)} px-3 py-2 outline-none focus:bg-white/5`}
            title={action.tooltip}
          >
            <span className="text-base">{action.icon}</span>
            <span>{action.label}</span>
          </DropdownMenuItem>
        ))}
        
        {actions.length > 0 && <DropdownMenuSeparator className="bg-white/10" />}
        
        <DropdownMenuItem
          onClick={() => handleSelect('copy_event_id')}
          className="text-[10px] text-slate-500 hover:text-slate-300 px-3 py-1.5 outline-none focus:bg-white/5 cursor-pointer"
        >
          Copiar ID: {event.id.slice(0, 8)}...
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
