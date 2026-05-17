export const SystemStatus = {
  CONNECTED: 'CONNECTED',
  DISCONNECTED: 'DISCONNECTED',
  DEGRADED: 'DEGRADED',
  RATE_LIMITED: 'RATE_LIMITED',
  PENDING: 'PENDING',
  EXPIRED: 'EXPIRED',
} as const;

export type SystemStatusType = typeof SystemStatus[keyof typeof SystemStatus];
