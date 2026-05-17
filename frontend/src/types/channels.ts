export type ChannelStatus = 
  | "disconnected"
  | "awaiting_qr_scan"
  | "pending_configuration"
  | "validating"
  | "connected"
  | "degraded"
  | "rate_limited"
  | "reconnecting"
  | "error"
  | "suspended";

export interface ChannelConfig {
  id: string;
  tenant_id: string;
  channel_type: string;
  status: ChannelStatus;
  external_session_id?: string;
  config: Record<string, any>;
  health_score: number;
  last_heartbeat?: string;
  created_at: string;
  updated_at: string;
}
