export type SourceType = 'sheets' | 'office' | 'local' | 'database' | 'ecommerce' | 'web';
export type SyncFrequency = 'manual' | 'hourly' | 'daily' | 'weekly' | 'realtime';

export interface IngestionState {
  step: number;
  sourceType: SourceType | null;
  connectionId: string | null;
  headers: string[];
  previewRows: Record<string, any>[];
  mapping: Record<string, string>;
  syncConfig: { frequency: SyncFrequency; agentId: string; conflictResolution: 'overwrite' | 'skip' };
  jobId: string | null;
  accountId: string | null;
  isProcessing: boolean;
  error: string | null;
}

export interface IngestionMetrics {
  total_tokens: number;
  active_products: number;
  total_chunks: number;
  success_rate: number;
  active_sources: number;
  last_sync_at: string | null;
  avg_index_time_seconds: number;
  dynamic_sources: number;
  static_sources: number;
}

export interface JobStatus {
  job_id: string;
  status: 'queued' | 'started' | 'syncing' | 'success' | 'failed';
  progress_percent: number;
  rows_processed: number;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
}
