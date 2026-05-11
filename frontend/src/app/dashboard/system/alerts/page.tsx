import React from "react";
import { SeverityBadge } from "@/components/ui/severity-badge";
import { ActionableButton } from "@/components/ui/actionable-button";
import type { Severity } from "@/components/ui/severity-badge";

// ─────────────────────────────────────────────
// Mock Data
// ─────────────────────────────────────────────
type AlertCategory = "inventory" | "payment" | "connector" | "system";

const categoryConfig: Record<AlertCategory, { icon: string; label: string }> = {
  inventory:  { icon: "📦", label: "Inventory" },
  payment:    { icon: "💳", label: "Payment" },
  connector:  { icon: "🔌", label: "Connector" },
  system:     { icon: "⚙️", label: "System" },
};

const mockAlerts = [
  {
    id: "alr_01",
    title: "Inventory Drift Detected",
    description: "Snapshot (5) ≠ Ledger calculation (4) for 'Vela Aromática Premium'. Delta +1. Requires snapshot rebuild.",
    severity: "CRITICAL" as Severity,
    category: "inventory" as AlertCategory,
    correlation_id: "integrity_run_07",
    at: "2 hrs ago",
    acknowledged: false,
    action_label: "Rebuild Snapshot",
  },
  {
    id: "alr_02",
    title: "Payment Failed — Retry Escalation",
    description: "txn_def456 exceeded 5 retry attempts and entered Dead Letter Queue. Manual replay required.",
    severity: "HIGH" as Severity,
    category: "payment" as AlertCategory,
    correlation_id: "txn_def456",
    at: "22 min ago",
    acknowledged: false,
    action_label: "Go to DLQ",
  },
  {
    id: "alr_03",
    title: "Connector Schema Changed",
    description: "'precio' column renamed to 'price_usd' in Google Sheets source. Sync paused. Schema validation failed.",
    severity: "HIGH" as Severity,
    category: "connector" as AlertCategory,
    correlation_id: "sync_job_44",
    at: "2 days ago",
    acknowledged: true,
    action_label: "Review Schema",
  },
  {
    id: "alr_04",
    title: "Webhook Duplicate Blocked",
    description: "MercadoPago resent event wh_103 3 times. All blocked by idempotency shield. No data corruption.",
    severity: "INFO" as Severity,
    category: "payment" as AlertCategory,
    correlation_id: "txn_def456",
    at: "20 min ago",
    acknowledged: true,
    action_label: undefined,
  },
];

const severityOrder: Record<Severity, number> = { CRITICAL: 0, HIGH: 1, WARNING: 2, INFO: 3 };
const sorted = [...mockAlerts].sort((a, b) => severityOrder[a.severity] - severityOrder[b.severity]);

// ─────────────────────────────────────────────
// Sub-components
// ─────────────────────────────────────────────
function AlertSummaryRow() {
  const counts = { CRITICAL: 0, HIGH: 0, WARNING: 0, INFO: 0 };
  mockAlerts.forEach(a => { if (!a.acknowledged) counts[a.severity]++; });

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {(["CRITICAL", "HIGH", "WARNING", "INFO"] as Severity[]).map(s => (
        <div key={s} className="bg-neutral-900 border border-neutral-800 rounded-xl p-5 flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-neutral-500 uppercase tracking-wider mb-1">{s}</p>
            <p className="text-3xl font-bold text-white">{counts[s]}</p>
          </div>
          <SeverityBadge severity={s} pulse={s === "CRITICAL" && counts[s] > 0} />
        </div>
      ))}
    </div>
  );
}

function AlertsFeed() {
  return (
    <div className="bg-neutral-900 border border-neutral-800 rounded-xl overflow-hidden">
      <div className="p-4 border-b border-neutral-800 flex justify-between items-center">
        <h2 className="text-sm font-semibold text-white">Operational Alerts</h2>
        <span className="text-xs text-neutral-500">{mockAlerts.filter(a => !a.acknowledged).length} unacknowledged</span>
      </div>

      <div className="flex flex-col divide-y divide-neutral-800">
        {sorted.map((alert) => {
          const cat = categoryConfig[alert.category];
          return (
            <div
              key={alert.id}
              className={`px-5 py-4 flex items-start justify-between gap-4 transition-colors
                ${alert.acknowledged ? "opacity-50 hover:opacity-70" : "hover:bg-neutral-800/20"}`}
            >
              <div className="flex items-start gap-4 flex-1 min-w-0">
                {/* Category icon */}
                <span className="text-2xl flex-shrink-0 mt-0.5">{cat.icon}</span>

                <div className="flex-1 min-w-0">
                  {/* Title row */}
                  <div className="flex flex-wrap items-center gap-2 mb-1.5">
                    <span className="text-sm font-semibold text-neutral-200">{alert.title}</span>
                    <SeverityBadge severity={alert.severity} pulse={!alert.acknowledged && alert.severity === "CRITICAL"} />
                    <span className="text-[9px] px-1.5 py-0.5 rounded border bg-neutral-800 text-neutral-500 border-neutral-700 uppercase">
                      {cat.label}
                    </span>
                    {alert.acknowledged && (
                      <span className="text-[9px] px-1.5 py-0.5 rounded border bg-emerald-500/10 text-emerald-600 border-emerald-800 uppercase">
                        Acknowledged
                      </span>
                    )}
                  </div>

                  {/* Description */}
                  <p className="text-xs text-neutral-400 leading-relaxed">{alert.description}</p>

                  {/* Meta */}
                  <div className="flex items-center gap-4 mt-2 text-[10px] text-neutral-600 font-mono">
                    <span>corr: {alert.correlation_id}</span>
                    <span>{alert.at}</span>
                  </div>
                </div>
              </div>

              {/* Actions */}
              {!alert.acknowledged && (
                <div className="flex flex-col items-end gap-2 flex-shrink-0">
                  {alert.action_label && (
                    <ActionableButton label={alert.action_label} icon="→" />
                  )}
                  <ActionableButton label="Acknowledge" icon="✓" variant="ghost" />
                </div>
              )}
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
export default function AlertsPage() {
  return (
    <div className="flex flex-col gap-6 p-8 min-h-screen bg-neutral-950 text-neutral-50 font-sans">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs text-neutral-500 mb-1">← Mission Control / System</p>
          <h1 className="text-2xl font-semibold text-white">Operational Alerts</h1>
          <p className="text-xs text-neutral-500 mt-1">
            Drift, failures, escalations — surfaced, not hidden.
          </p>
        </div>
      </div>

      <AlertSummaryRow />
      <AlertsFeed />
    </div>
  );
}
