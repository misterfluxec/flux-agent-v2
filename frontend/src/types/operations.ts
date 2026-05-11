export type TimelineCategory = 'interaction' | 'commerce' | 'ops' | 'automation' | 'system' | 'billing';
export type AggregateType = 'lead' | 'quote' | 'order' | 'booking' | 'conversation' | 'system';
export type EventSeverity = 'low' | 'medium' | 'high' | 'critical';
export type AckState = 'unresolved' | 'acknowledged' | 'snoozed' | 'resolved';

export interface EventAggregate {
  type: AggregateType;
  id: string;
}

export interface TimelineEvent {
  id: string;
  type: string;
  timestamp: string; // ISO 8601
  category: TimelineCategory;
  severity: EventSeverity;
  business_impact?: string | null;
  summary: string;
  correlation_id?: string | null;
  aggregate?: EventAggregate; // Present in global timeline
  payload?: Record<string, any>; // Present when requested specifically or in websocket
  
  // Enriched fields from migration 011
  priority_score?: number;
  tags?: string[];
  ack_state?: AckState;
  assigned_to?: string | null;
  assigned_team?: string | null;

  // Realtime Reconciliation (Sprint 4.3)
  updated_at?: string;
  updated_by?: {
    id: string;
    name: string;
    type: 'human_operator' | 'ai_agent' | 'system';
  };
  mutation_source_id?: string;
  version?: number;
}

export interface OperationalHealthCheck {
  check: string;
  status: 'ok' | 'warning' | 'degraded' | 'critical';
  message: string;
  details: Record<string, any>;
}

export interface OperationalHealthReport {
  tenant_id: string;
  evaluated_at: string;
  overall_status: 'ok' | 'warning' | 'degraded' | 'critical';
  critical_count: number;
  warning_count: number;
  checks: OperationalHealthCheck[];
  requires_attention: OperationalHealthCheck[];
}

export interface AckRequest {
  state: AckState;
  snooze_minutes?: number;
}

export interface AssignRequest {
  assigned_to?: string;
  assigned_team?: string;
}

export interface TagRequest {
  add?: string[];
  remove?: string[];
}

export interface ActionDefinition {
  id: string;
  label: string;
  icon: string;
  variant: 'primary' | 'secondary' | 'warning' | 'danger';
  requires_confirmation?: boolean;
  confirmation_message?: string;
  enabled: boolean;
  tooltip?: string;
}

// Sprint 4.3 Context Intelligence
export interface EntityIntelligence {
  aggregate_id: string;
  aggregate_type: string;
  ltv: number;
  churn_risk: 'low' | 'medium' | 'high';
  sentiment: 'positive' | 'neutral' | 'negative';
  sla_deadline?: string; // ISO string if there is a pending SLA
  active_playbook?: string;
  next_best_action?: {
    action: string;
    confidence: number;
    reason: string;
  };
  operator_notes: string;
}
