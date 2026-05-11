import { api } from './client';
import { 
  TimelineEvent, 
  OperationalHealthReport, 
  AckRequest, 
  AssignRequest, 
  TagRequest,
  AggregateType,
  EntityIntelligence
} from '@/types/operations';

export const getEntityIntelligence = async (aggregateType: AggregateType, aggregateId: string) => {
  // Mock endpoint for Sprint 4.3 since backend intelligence endpoint is not ready yet
  return {
    aggregate_id: aggregateId,
    aggregate_type: aggregateType,
    ltv: 12500,
    churn_risk: 'low',
    sentiment: 'positive',
    sla_deadline: new Date(Date.now() + 2 * 3600000).toISOString(), // 2 hours from now
    active_playbook: 'Premium Onboarding',
    next_best_action: {
      action: 'Agendar llamada de seguimiento',
      confidence: 85,
      reason: 'Cliente demostró alto interés en la última interacción'
    },
    operator_notes: 'Cliente muy interesado en integraciones de WhatsApp. Prefiere demos cortas.'
  } as EntityIntelligence;
};

export interface TimelinePage {
  events: TimelineEvent[];
  next_cursor?: number;
  has_more: boolean;
}

export const getEntityTimeline = async (aggregateType: AggregateType, aggregateId: string, limit: number = 50, cursor: number = 0) => {
  const data = await api.get<TimelineEvent[]>(`/api/v1/operations/${aggregateType}/${aggregateId}/timeline?limit=${limit}`);
  return {
    events: data || [],
    has_more: false // backend no soporta paginación aún
  } as TimelinePage;
};

export const getGlobalTimeline = async (eventTypes?: string, severity?: string, limit: number = 50, cursor: number = 0) => {
  let url = `/api/v1/operations/timeline?limit=${limit}`;
  if (eventTypes) url += `&event_types=${eventTypes}`;
  if (severity) url += `&severity=${severity}`;
  const data = await api.get<TimelineEvent[]>(url);
  return {
    events: data || [],
    has_more: false // backend no soporta paginación aún
  } as TimelinePage;
};

export const getOperationalHealth = () => {
  return api.get<OperationalHealthReport>('/api/v1/health/operational');
};

export const getPriorityQueue = (limit: number = 20, tags?: string) => {
  let url = `/api/v1/events/priority-queue?limit=${limit}`;
  if (tags) url += `&tags=${tags}`;
  return api.get<TimelineEvent[]>(url);
};

export const acknowledgeEvent = (eventId: string, data: AckRequest) => {
  return api.patch<any>(`/api/v1/events/${eventId}/ack`, data); 
};

export const assignEvent = (eventId: string, data: AssignRequest) => {
  return api.patch<any>(`/api/v1/events/${eventId}/assign`, data); 
};

export const updateEventTags = (eventId: string, data: TagRequest) => {
  return api.patch<any>(`/api/v1/events/${eventId}/tags`, data); 
};
