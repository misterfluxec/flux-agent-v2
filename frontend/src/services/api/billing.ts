/**
 * billing.ts — API Service para Facturación y Planes
 * Conecta con: plans_router, billing_router, invoices_router, usage_router, quota_router
 */

import { apiClient } from "@/lib/api-client";

// ─── Types ─────────────────────────────────────────────────────────────────

export type PlanTier = "starter" | "pro" | "enterprise";

export interface Plan {
  id: string;
  name: string;
  tier: PlanTier;
  price_monthly: number;
  price_annual: number;
  limits: {
    max_agents: number;
    max_messages_month: number;
    max_whatsapp_instances: number;
    knowledge_base_mb: number;
    rag_queries_month: number;
  };
  features: string[];
  is_current: boolean;
}

export interface CurrentPlan {
  tier: PlanTier;
  name: string;
  started_at: string;
  renews_at: string;
  is_annual: boolean;
  price_paid: number;
}

export interface UsageMetrics {
  period_start: string;
  period_end: string;
  messages_used: number;
  messages_limit: number;
  messages_pct: number;
  agents_used: number;
  agents_limit: number;
  whatsapp_instances_used: number;
  whatsapp_instances_limit: number;
  knowledge_base_mb_used: number;
  knowledge_base_mb_limit: number;
  rag_queries_used: number;
  rag_queries_limit: number;
}

export interface Invoice {
  id: string;
  period: string;
  amount: number;
  currency: string;
  status: "paid" | "pending" | "failed" | "draft";
  issued_at: string;
  paid_at?: string;
  pdf_url?: string;
  items: { description: string; amount: number }[];
}

export interface UpgradePreview {
  from_plan: PlanTier;
  to_plan: PlanTier;
  proration_credit: number;
  new_monthly_price: number;
  effective_date: string;
}

// ─── API Functions ──────────────────────────────────────────────────────────

/** Lista todos los planes disponibles */
export async function getPlans(): Promise<Plan[]> {
  const res = await apiClient.get<Plan[]>("/plans");
  return res.data;
}

/** Plan is_active del tenant actual */
export async function getCurrentPlan(): Promise<CurrentPlan> {
  const res = await apiClient.get<CurrentPlan>("/plans/active");
  return res.data;
}

/** Métricas de uso del período actual */
export async function getUsageMetrics(): Promise<UsageMetrics> {
  const res = await apiClient.get<UsageMetrics>("/usage/current");
  return res.data;
}

/** Historial de facturas */
export async function getInvoices(limit = 12): Promise<Invoice[]> {
  const res = await apiClient.get<Invoice[]>(`/invoices?limit=${limit}`);
  return res.data;
}

/** Previsualizar costo de upgrade */
export async function previewUpgrade(targetPlan: PlanTier): Promise<UpgradePreview> {
  const res = await apiClient.post<UpgradePreview>("/plans/upgrade/preview", {
    target_plan: targetPlan,
  });
  return res.data;
}

/** Confirmar upgrade de plan */
export async function upgradePlan(
  targetPlan: PlanTier,
  annual: boolean
): Promise<{ success: boolean; redirect_url?: string }> {
  const res = await apiClient.post<{ success: boolean; redirect_url?: string }>(
    "/plans/upgrade",
    { target_plan: targetPlan, annual }
  );
  return res.data;
}

/** Límites de cuota actuales */
export async function getQuotaStatus(): Promise<{
  at_limit: boolean;
  warnings: { resource: string; used_pct: number; message: string }[];
}> {
  const res = await apiClient.get<{
    at_limit: boolean;
    warnings: { resource: string; used_pct: number; message: string }[];
  }>("/quota/status");
  return res.data;
}
