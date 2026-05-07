export type ConnectorType = 'shopify' | 'woocommerce' | 'webchat';
export type SyncStatus = 'pending' | 'syncing' | 'active' | 'error' | 'paused';

export interface ConnectorConfig {
  id: string;
  type: ConnectorType;
  status: SyncStatus;
  storeUrl: string;
  apiKey?: string; // Se guarda cifrado en BD
  webhookSecret?: string;
  productsSynced: number;
  lastSync?: string;
  autoSync: boolean;
}

export interface ROIMetrics {
  conversations: number;
  qualifiedLeads: number;
  salesAttributed: number;
  conversionRate: number;
  revenueAttributed: number;
  avgOrderValue: number;
  trend: number; // % vs período anterior
}

export const MOCK_CONNECTORS: ConnectorConfig[] = [
  { id: '1', type: 'shopify', status: 'active', storeUrl: 'https://mitienda.myshopify.com', productsSynced: 142, lastSync: '2026-05-05T12:00:00Z', autoSync: true },
  { id: '2', type: 'woocommerce', status: 'error', storeUrl: 'https://mitienda.com', productsSynced: 87, lastSync: '2026-05-04T18:30:00Z', autoSync: true },
  { id: '3', type: 'webchat', status: 'active', storeUrl: 'N/A', productsSynced: 0, autoSync: false }
];

export const MOCK_ROI: ROIMetrics = {
  conversations: 1240, qualifiedLeads: 380, salesAttributed: 94,
  conversionRate: 7.6, revenueAttributed: 12450.00, avgOrderValue: 132.45, trend: 12.4
};
