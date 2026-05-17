/**
 * Feature Registry
 * Defines all available features and capabilities in the system.
 * Used for RBAC, feature flags, and UI gating.
 */

export type FeatureFlag = 
  | 'view_dashboard'
  | 'view_operations'
  | 'view_catalog'
  | 'view_quotes'
  | 'view_orders'
  | 'view_crm'
  | 'create_leads'
  | 'manage_crm_pipeline'
  | 'manage_connections'
  | 'view_analytics'
  | 'manage_agents'
  | 'manage_channels'
  | 'manage_flows'
  | 'billing_access'
  | 'admin_settings';

export const FEATURE_REGISTRY: Record<FeatureFlag, { description: string; requiredPlan: 'starter' | 'pro' | 'enterprise' }> = {
  view_dashboard: { description: 'Access main dashboard', requiredPlan: 'starter' },
  view_operations: { description: 'Access conversations/operations', requiredPlan: 'starter' },
  view_catalog: { description: 'Access product catalog', requiredPlan: 'starter' },
  view_quotes: { description: 'Access quotes system', requiredPlan: 'starter' },
  view_orders: { description: 'Access orders management', requiredPlan: 'starter' },
  view_crm: { description: 'Access CRM pipeline', requiredPlan: 'starter' },
  create_leads: { description: 'Create new leads in CRM', requiredPlan: 'starter' },
  manage_crm_pipeline: { description: 'Move leads across stages', requiredPlan: 'starter' },
  manage_connections: { description: 'Manage ETL/Integrations', requiredPlan: 'pro' },
  view_analytics: { description: 'Access advanced analytics', requiredPlan: 'pro' },
  manage_agents: { description: 'Manage AI Agents', requiredPlan: 'starter' },
  manage_channels: { description: 'Manage communication channels', requiredPlan: 'starter' },
  manage_flows: { description: 'Manage automated workflows', requiredPlan: 'pro' },
  billing_access: { description: 'Access operational billing', requiredPlan: 'pro' },
  admin_settings: { description: 'Access tenant settings', requiredPlan: 'starter' }
};

export function isFeatureEnabled(feature: FeatureFlag, currentPlan: string): boolean {
  const featureConfig = FEATURE_REGISTRY[feature];
  if (!featureConfig) return false;
  
  const planHierarchy = { starter: 0, pro: 1, enterprise: 2 };
  const userPlanLevel = planHierarchy[currentPlan as keyof typeof planHierarchy] ?? 0;
  const reqPlanLevel = planHierarchy[featureConfig.requiredPlan as keyof typeof planHierarchy] ?? 0;
  
  return userPlanLevel >= reqPlanLevel;
}
