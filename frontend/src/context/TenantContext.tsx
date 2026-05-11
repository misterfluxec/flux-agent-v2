// =============================================================================
// TENANT CONTEXT — Plan del tenant cacheado desde /billing/subscription
// Decisión: billing_router (no JWT) para permitir cambios de plan sin re-login
// =============================================================================

"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { api } from "@/lib/api";
import { normalizePlan, TenantPlan } from "@/config/flags";

interface TenantContextValue {
  plan: TenantPlan;
  tenantId: string | null;
  tenantName: string | null;
  isLoading: boolean;
  refetch: () => void;
}

const TenantContext = createContext<TenantContextValue>({
  plan: "starter",
  tenantId: null,
  tenantName: null,
  isLoading: true,
  refetch: () => {},
});

export function TenantProvider({ children }: { children: ReactNode }) {
  const [plan, setPlan] = useState<TenantPlan>("starter");
  const [tenantId, setTenantId] = useState<string | null>(null);
  const [tenantName, setTenantName] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchPlan = async () => {
    // Skip if no token — avoid 401 storm on public pages (login, landing, register)
    const token = typeof window !== "undefined" ? localStorage.getItem("flux_token") : null;
    if (!token) {
      setIsLoading(false);
      return;
    }
    try {
      const { data } = await api.get("/billing/subscription");
      setPlan(normalizePlan(data?.plan || data?.plan_id));
      setTenantId(data?.tenant_id ?? null);
      setTenantName(data?.company_name ?? data?.tenant_name ?? null);
    } catch {
      // Fallback seguro: starter (nunca bloquear la app)
      setPlan("starter");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchPlan();
    // Refetch cada 5 minutos para capturar upgrades sin re-login
    const interval = setInterval(fetchPlan, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <TenantContext.Provider value={{ plan, tenantId, tenantName, isLoading, refetch: fetchPlan }}>
      {children}
    </TenantContext.Provider>
  );
}

export function useTenant(): TenantContextValue {
  return useContext(TenantContext);
}
