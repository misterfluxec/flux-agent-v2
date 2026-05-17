/**
 * connectors.ts — API Service para el Motor de Conectores
 * Conecta el frontend con los conectores reales del backend:
 *   - SQL Server (connectors/legacy/sqlserver.py)
 *   - CSV/Excel (connectors/legacy/csv_excel.py)
 *   - Google Sheets (connectors/v2/google_sheets.py)
 * Backend routes: /api/v1/connectors/{provider}/test | sync
 */

import { apiClient } from "@/lib/api-client";

// ─── Types ─────────────────────────────────────────────────────────────────

export type ConnectorProvider =
  | "sqlserver"
  | "csv_excel"
  | "google_sheets"
  | "mysql"
  | "postgresql";

export type SyncStatus = "idle" | "syncing" | "success" | "error" | "scheduled";

export interface ConnectorConfig {
  tenant_id: string;
  provider: ConnectorProvider;
  host?: string;
  port?: number;
  database?: string;
  username?: string;
  password?: string;
  file_path?: string;
  sheet_name?: string;
  spreadsheet_id?: string;
  range?: string;
  oauth_token?: string;
  sync_customers?: boolean;
  sync_products?: boolean;
  sync_orders?: boolean;
}

export interface ConnectorCapabilities {
  customers: boolean;
  products: boolean;
  orders: boolean;
  inventory: boolean;
}

export interface ConnectorTestResult {
  success: boolean;
  message: string;
  capabilities: ConnectorCapabilities;
  schema_preview?: Record<string, string[]>;
  error?: string;
}

export interface SyncResult {
  status: "sync_queued" | "sync_failed";
  provider: ConnectorProvider;
  message: string;
  job_id?: string;
}

export interface ConnectorStatus {
  id: string;
  provider: ConnectorProvider;
  name: string;
  status: SyncStatus;
  last_sync_at?: string;
  last_sync_records?: number;
  next_sync_at?: string;
  error_message?: string;
  capabilities: ConnectorCapabilities;
}

export interface SyncLog {
  id: string;
  connector_id: string;
  provider: ConnectorProvider;
  started_at: string;
  completed_at?: string;
  records_synced: number;
  status: "success" | "error" | "partial";
  error_message?: string;
}

// ─── API Functions ──────────────────────────────────────────────────────────

/** Prueba la conexión con un ERP/fuente de datos */
export async function testConnectorConnection(
  provider: ConnectorProvider,
  config: ConnectorConfig
): Promise<ConnectorTestResult> {
  const res = await apiClient.post<ConnectorTestResult>(
    `/connectors/${provider}/test`,
    config
  );
  return res.data;
}

/** Inicia sincronización completa en background */
export async function triggerSync(
  provider: ConnectorProvider,
  config: ConnectorConfig
): Promise<SyncResult> {
  const res = await apiClient.post<SyncResult>(`/connectors/${provider}/sync`, config);
  return res.data;
}

/** Lista todos los conectores activos del tenant */
export async function listConnectors(): Promise<ConnectorStatus[]> {
  const res = await apiClient.get<ConnectorStatus[]>("/connectors");
  return res.data;
}

/** Historial de sincronizaciones de un conector */
export async function getConnectorLogs(
  connectorId: string,
  limit = 20
): Promise<SyncLog[]> {
  const res = await apiClient.get<SyncLog[]>(`/connectors/${connectorId}/logs?limit=${limit}`);
  return res.data;
}

/** Elimina/desconecta un conector configurado */
export async function deleteConnector(
  connectorId: string
): Promise<{ success: boolean }> {
  const res = await apiClient.delete<{ success: boolean }>(`/connectors/${connectorId}`);
  return res.data;
}

/** Metadatos de providers soportados para la UI del Wizard */
export const SUPPORTED_PROVIDERS: {
  id: ConnectorProvider;
  name: string;
  description: string;
  icon: string;
  category: "database" | "file" | "cloud";
}[] = [
  {
    id: "sqlserver",
    name: "SQL Server",
    description: "Conecta tu ERP o base de datos Microsoft SQL Server",
    icon: "🗄️",
    category: "database",
  },
  {
    id: "mysql",
    name: "MySQL / MariaDB",
    description: "Base de datos MySQL o MariaDB on-premise o en la nube",
    icon: "🐬",
    category: "database",
  },
  {
    id: "csv_excel",
    name: "CSV / Excel",
    description: "Importa catálogos, listas de clientes desde archivos Excel o CSV",
    icon: "📊",
    category: "file",
  },
  {
    id: "google_sheets",
    name: "Google Sheets",
    description: "Sincroniza tu catálogo directamente desde Google Sheets",
    icon: "📋",
    category: "cloud",
  },
];
