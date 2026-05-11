import React from "react";
import { SeverityBadge } from "@/components/ui/severity-badge";
import { ActionableButton } from "@/components/ui/actionable-button";
import type { Severity } from "@/components/ui/severity-badge";

// ─────────────────────────────────────────────
// Mock Data
// ─────────────────────────────────────────────
const mockCustomer = {
  id: "cust_001",
  name: "Laura González",
  email: "laura.g@ejemplo.com",
  health_score: 78,
  ltv: 1240.50,
  total_orders: 8,
  failed_payments_30d: 2,
  risk_level: "MEDIUM",
};

type TimelineEventType = "order.created" | "payment.completed" | "payment.failed" | "inventory.reserved" | "copilot.alert.churn_risk" | "connector.sync.completed";

const timelineEventConfig: Record<TimelineEventType, { icon: string; color: string; label: string }> = {
  "order.created":              { icon: "🛒", color: "border-blue-500/40",    label: "Order Created" },
  "payment.completed":          { icon: "✅", color: "border-emerald-500/40", label: "Payment Completed" },
  "payment.failed":             { icon: "❌", color: "border-rose-500/40",    label: "Payment Failed" },
  "inventory.reserved":         { icon: "📦", color: "border-blue-500/30",    label: "Inventory Reserved" },
  "copilot.alert.churn_risk":   { icon: "🤖", color: "border-amber-500/40",   label: "AI Copilot Alert" },
  "connector.sync.completed":   { icon: "🔄", color: "border-neutral-600",    label: "Sync Completed" },
};

const mockTimeline: Array<{
  id: string; type: TimelineEventType; at: string;
  severity: Severity; description: string; correlation_id: string; replayable: boolean;
}> = [
  { id: "tl_01", type: "copilot.alert.churn_risk", at: "1 hr ago", severity: "WARNING", description: "Copilot detectó 72% de riesgo de abandono. Sugerencia: enviar cupón de retención.", correlation_id: "copilot_run_12", replayable: false },
  { id: "tl_02", type: "payment.failed", at: "2 hrs ago", severity: "HIGH", description: "Pago rechazado por fondos insuficientes. Webhook recibido con 2 retries.", correlation_id: "txn_def456", replayable: true },
  { id: "tl_03", type: "inventory.reserved", at: "2 hrs ago", severity: "INFO", description: "SOFT reservation: Kit Aromaterapia ×1 por 30 min.", correlation_id: "txn_def456", replayable: false },
  { id: "tl_04", type: "order.created", at: "2 hrs ago", severity: "INFO", description: "Orden ORD-9902 creada tras conversión de cotización CQT-4401.", correlation_id: "txn_def456", replayable: false },
  { id: "tl_05", type: "payment.completed", at: "3 days ago", severity: "INFO", description: "Pago $350 confirmado vía MercadoPago. Sin retries.", correlation_id: "txn_abc123", replayable: false },
];

// ─────────────────────────────────────────────
// Sub-components
// ─────────────────────────────────────────────
function CustomerHealthCard() {
  const { name, email, health_score, ltv, total_orders, failed_payments_30d, risk_level } = mockCustomer;
  const healthColor = health_score >= 80 ? "text-emerald-400" : health_score >= 60 ? "text-amber-400" : "text-rose-400";

  return (
    <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-6 grid grid-cols-2 md:grid-cols-4 gap-6">
      {/* Customer identity */}
      <div className="col-span-2 md:col-span-1 flex flex-col justify-center border-r border-neutral-800 pr-6">
        <div className="h-12 w-12 rounded-full bg-neutral-800 flex items-center justify-center text-xl font-bold text-white mb-3">
          {name[0]}
        </div>
        <p className="text-lg font-semibold text-white">{name}</p>
        <p className="text-xs text-neutral-500">{email}</p>
      </div>

      {/* Health Score */}
      <div className="flex flex-col justify-center border-r border-neutral-800 pr-6">
        <p className="text-xs font-semibold text-neutral-500 uppercase tracking-wider mb-1">Health Score</p>
        <p className={`text-4xl font-bold tracking-tight ${healthColor}`}>{health_score}<span className="text-xl">%</span></p>
        <p className="text-xs text-neutral-600 mt-1">Operational Relationship</p>
      </div>

      {/* Payment reliability */}
      <div className="flex flex-col justify-center border-r border-neutral-800 pr-6">
        <p className="text-xs font-semibold text-neutral-500 uppercase tracking-wider mb-1">Payment Reliability</p>
        <p className="text-2xl font-bold text-white">${ltv.toFixed(0)} LTV</p>
        <p className="text-xs text-amber-400 mt-1">{failed_payments_30d} failed in last 30d</p>
      </div>

      {/* Operational Risk */}
      <div className="flex flex-col justify-center">
        <p className="text-xs font-semibold text-neutral-500 uppercase tracking-wider mb-2">Operational Risk</p>
        <SeverityBadge severity="WARNING" />
        <p className="text-xs text-neutral-600 mt-2">{total_orders} total orders</p>
      </div>
    </div>
  );
}

function OperationalTimeline() {
  return (
    <div className="bg-neutral-900 border border-neutral-800 rounded-xl overflow-hidden">
      <div className="p-4 border-b border-neutral-800">
        <h2 className="text-sm font-semibold text-white">Operational Timeline</h2>
        <p className="text-xs text-neutral-600 mt-0.5">All events across payments, orders, AI alerts, and sync history.</p>
      </div>

      <div className="relative flex flex-col">
        {/* Vertical timeline line */}
        <div className="absolute left-8 top-0 bottom-0 w-px bg-neutral-800"></div>

        {mockTimeline.map((evt) => {
          const config = timelineEventConfig[evt.type];
          return (
            <div key={evt.id} className={`relative pl-16 pr-6 py-4 border-l-2 ml-8 ${config.color} hover:bg-neutral-800/20 transition-colors`}>
              {/* Icon bubble */}
              <span className="absolute -left-5 top-4 flex items-center justify-center h-8 w-8 rounded-full bg-neutral-900 border border-neutral-800 text-base">
                {config.icon}
              </span>

              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-medium text-neutral-200">{config.label}</span>
                    <SeverityBadge severity={evt.severity} pulse={evt.severity === "CRITICAL"} />
                  </div>
                  <p className="text-sm text-neutral-400">{evt.description}</p>
                  <p className="text-xs text-neutral-600 font-mono mt-1">
                    corr: {evt.correlation_id} · {evt.at}
                  </p>
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                  {evt.replayable && (
                    <ActionableButton label="Replay" icon="↻" />
                  )}
                  <ActionableButton label="Inspect" icon="⬡" variant="ghost" />
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────
// Page
// ─────────────────────────────────────────────
interface Props {
  params: { id: string };
}

export default function Customer360Page({ params }: Props) {
  return (
    <div className="flex flex-col gap-6 p-8 min-h-screen bg-neutral-950 text-neutral-50 font-sans">
      <div>
        <p className="text-xs text-neutral-500 mb-1">← Mission Control</p>
        <h1 className="text-2xl font-semibold text-white">Customer 360°</h1>
        <p className="text-xs text-neutral-500 font-mono mt-1">ID: {params.id}</p>
      </div>

      <CustomerHealthCard />
      <OperationalTimeline />
    </div>
  );
}
