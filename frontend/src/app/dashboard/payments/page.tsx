import React from "react";
import { SeverityBadge } from "@/components/ui/severity-badge";
import { ActionableButton } from "@/components/ui/actionable-button";
import type { Severity } from "@/components/ui/severity-badge";

// ─────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────
type PaymentStatus = "authorized" | "processing" | "paid" | "failed" | "refunded" | "chargeback";

const paymentStatusConfig: Record<PaymentStatus, { label: string; color: string }> = {
  authorized: { label: "Authorized",  color: "text-blue-400" },
  processing: { label: "Processing",  color: "text-amber-400" },
  paid:       { label: "Paid",        color: "text-emerald-400" },
  failed:     { label: "Failed",      color: "text-rose-400" },
  refunded:   { label: "Refunded",    color: "text-purple-400" },
  chargeback: { label: "Chargeback",  color: "text-orange-400" },
};

// ─────────────────────────────────────────────
// Mock Data
// ─────────────────────────────────────────────
const mockPayments = [
  { id: "pi_001", order_ref: "ORD-9901", amount: 350.00, status: "paid" as PaymentStatus, gateway: "mercadopago", correlation_id: "txn_abc123", webhook_retries: 0, created_at: "2 min ago", severity: "INFO" as Severity },
  { id: "pi_002", order_ref: "ORD-9902", amount: 120.50, status: "failed" as PaymentStatus, gateway: "mercadopago", correlation_id: "txn_def456", webhook_retries: 3, created_at: "18 min ago", severity: "HIGH" as Severity },
  { id: "pi_003", order_ref: "ORD-9893", amount: 890.00, status: "chargeback" as PaymentStatus, gateway: "mercadopago", correlation_id: "txn_ghi789", webhook_retries: 0, created_at: "1 hr ago", severity: "CRITICAL" as Severity },
  { id: "pi_004", order_ref: "ORD-9888", amount: 55.00, status: "refunded" as PaymentStatus, gateway: "mercadopago", correlation_id: "txn_jkl012", webhook_retries: 1, created_at: "3 hrs ago", severity: "WARNING" as Severity },
  { id: "pi_005", order_ref: "ORD-9879", amount: 200.00, status: "authorized" as PaymentStatus, gateway: "mercadopago", correlation_id: "txn_mno345", webhook_retries: 0, created_at: "5 hrs ago", severity: "INFO" as Severity },
];

const mockWebhooks = [
  { event_id: "wh_101", type: "payment.updated", status: "processed", retry_count: 0, duplicate: false, received_at: "2 min ago", correlation_id: "txn_abc123" },
  { event_id: "wh_102", type: "payment.updated", status: "failed", retry_count: 3, duplicate: false, received_at: "18 min ago", correlation_id: "txn_def456" },
  { event_id: "wh_103", type: "payment.updated", status: "ignored", retry_count: 0, duplicate: true, received_at: "20 min ago", correlation_id: "txn_def456" },
  { event_id: "wh_104", type: "payment.updated", status: "processed", retry_count: 0, duplicate: false, received_at: "1 hr ago", correlation_id: "txn_ghi789" },
];

// ─────────────────────────────────────────────
// Sub-components
// ─────────────────────────────────────────────
function ConsoleMetricCard({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5">
      <p className="text-xs font-semibold text-neutral-500 uppercase tracking-wider mb-2">{label}</p>
      <p className="text-3xl font-bold text-white tracking-tight">{value}</p>
      {sub && <p className="text-xs text-neutral-500 mt-1">{sub}</p>}
    </div>
  );
}

function PaymentLifecycleTable() {
  return (
    <div className="bg-neutral-900 border border-neutral-800 rounded-xl overflow-hidden">
      <div className="p-4 border-b border-neutral-800 flex justify-between items-center">
        <h2 className="text-sm font-semibold text-white">Payment Lifecycle</h2>
        <span className="text-xs text-neutral-500 font-mono">Last 24h · {mockPayments.length} records</span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-neutral-800">
              {["Intent ID", "Order", "Amount", "Status", "Severity", "Retries", "Correlation", ""].map(h => (
                <th key={h} className="text-left px-4 py-3 text-xs font-semibold text-neutral-500 uppercase tracking-wide">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {mockPayments.map((p) => {
              const s = paymentStatusConfig[p.status];
              return (
                <tr key={p.id} className="border-b border-neutral-800/50 hover:bg-neutral-800/30 transition-colors">
                  <td className="px-4 py-3 font-mono text-xs text-neutral-400">{p.id}</td>
                  <td className="px-4 py-3 text-neutral-300">{p.order_ref}</td>
                  <td className="px-4 py-3 font-semibold text-white">${p.amount.toFixed(2)}</td>
                  <td className="px-4 py-3">
                    <span className={`font-semibold ${s.color}`}>{s.label}</span>
                  </td>
                  <td className="px-4 py-3">
                    <SeverityBadge severity={p.severity} pulse={p.severity === "CRITICAL"} />
                  </td>
                  <td className="px-4 py-3 text-neutral-400">
                    {p.webhook_retries > 0 
                      ? <span className="text-amber-400 font-semibold">{p.webhook_retries} retries</span> 
                      : <span className="text-neutral-600">—</span>}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-neutral-500">{p.correlation_id}</td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      {p.status === "failed" && (
                        <ActionableButton label="Retry Webhook" icon="↻" />
                      )}
                      <ActionableButton label="Inspect" icon="⬡" variant="ghost" />
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function WebhookTimeline() {
  return (
    <div className="bg-neutral-900 border border-neutral-800 rounded-xl overflow-hidden">
      <div className="p-4 border-b border-neutral-800">
        <h2 className="text-sm font-semibold text-white">Webhook Timeline</h2>
      </div>
      <div className="flex flex-col divide-y divide-neutral-800">
        {mockWebhooks.map((wh) => (
          <div key={wh.event_id} className="px-4 py-3 flex items-center justify-between hover:bg-neutral-800/30 transition-colors">
            <div className="flex items-center gap-4">
              {/* Status dot */}
              <span className={`h-2 w-2 rounded-full flex-shrink-0 ${
                wh.status === "processed" ? "bg-emerald-500" :
                wh.status === "failed"    ? "bg-rose-500" :
                "bg-neutral-600"
              }`}></span>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-mono text-neutral-300">{wh.type}</span>
                  {wh.duplicate && (
                    <span className="text-[9px] uppercase font-bold px-1.5 py-0.5 rounded bg-neutral-800 text-neutral-500 border border-neutral-700">
                      DUPLICATE BLOCKED
                    </span>
                  )}
                  {wh.retry_count > 0 && (
                    <span className="text-[9px] px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">
                      {wh.retry_count} retries
                    </span>
                  )}
                </div>
                <div className="text-xs text-neutral-600 font-mono mt-0.5">
                  corr: {wh.correlation_id} · {wh.received_at}
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {wh.status === "failed" && (
                <ActionableButton label="Replay" icon="↻" />
              )}
              <ActionableButton label="Payload" icon="{ }" variant="ghost" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────
// Page
// ─────────────────────────────────────────────
export default function PaymentConsolePage() {
  return (
    <div className="flex flex-col gap-6 p-8 min-h-screen bg-neutral-950 text-neutral-50 font-sans">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs text-neutral-500 mb-1">← Mission Control</p>
          <h1 className="text-2xl font-semibold text-white">Payment Operations Console</h1>
        </div>
        <SeverityBadge severity="HIGH" pulse />
      </div>

      {/* KPI row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <ConsoleMetricCard label="Success Rate (24h)" value="97.8%" sub="↑ from 96.2% yesterday" />
        <ConsoleMetricCard label="Total Revenue (24h)" value="$12,450" sub="38 transactions" />
        <ConsoleMetricCard label="Webhook Reliability" value="99.1%" sub="2 failed, 1 duplicate blocked" />
        <ConsoleMetricCard label="Chargebacks" value="1" sub="⚠ Requires review" />
      </div>

      {/* Lifecycle Table */}
      <PaymentLifecycleTable />

      {/* Webhook Timeline */}
      <WebhookTimeline />
    </div>
  );
}
