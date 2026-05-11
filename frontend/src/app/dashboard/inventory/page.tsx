import React from "react";
import { SeverityBadge } from "@/components/ui/severity-badge";
import { ActionableButton } from "@/components/ui/actionable-button";
import type { Severity } from "@/components/ui/severity-badge";

// ─────────────────────────────────────────────
// Mock Data
// ─────────────────────────────────────────────
const mockLedgerEntries = [
  { id: "led_01", product: "Vela Aromática Premium", movement_type: "COMMIT", qty: -2, reason: "Order Fulfilled", correlation_id: "txn_abc123", at: "2 min ago", severity: "INFO" as Severity },
  { id: "led_02", product: "Vela Aromática Premium", movement_type: "RESERVE", qty: -1, reason: "Cart Reservation", correlation_id: "txn_def456", at: "15 min ago", severity: "INFO" as Severity },
  { id: "led_03", product: "Difusor Bambú", movement_type: "RELEASE", qty: +1, reason: "Reservation Expired", correlation_id: "corr_exp_001", at: "22 min ago", severity: "WARNING" as Severity },
  { id: "led_04", product: "Vela Aromática Premium", movement_type: "SYNC_CORRECTION", qty: +1, reason: "ERP Reconciliation (ERP_WINS)", correlation_id: "sync_job_44", at: "1 hr ago", severity: "WARNING" as Severity },
];

const mockReservations = [
  { id: "res_01", product: "Kit Aromaterapia", type: "SOFT", qty: 3, expires_in: "42 min", customer: "Laura G.", correlation_id: "txn_xyz999" },
  { id: "res_02", product: "Vela Aromática Premium", type: "HARD", qty: 2, expires_in: "—", customer: "José M.", correlation_id: "txn_abc123" },
  { id: "res_03", product: "Difusor Bambú", type: "SOFT", qty: 1, expires_in: "8 min", customer: "Guest", correlation_id: "txn_anon_7" },
];

const mockDrifts = [
  { product: "Vela Aromática Premium", snapshot: 5, ledger_calc: 4, delta: 1, status: "UNRESOLVED", detected_at: "2 hrs ago" },
];

const movementColor: Record<string, string> = {
  COMMIT:          "text-emerald-400",
  RESERVE:         "text-blue-400",
  RELEASE:         "text-amber-400",
  SYNC_CORRECTION: "text-orange-400",
  ADJUSTMENT:      "text-neutral-400",
};

// ─────────────────────────────────────────────
// Sub-components
// ─────────────────────────────────────────────
function StockSummaryRow() {
  return (
    <div className="grid grid-cols-3 gap-4">
      {[
        { label: "Total Stock",    value: "248",  sub: "all products" },
        { label: "Hard Reserved", value: "12",   sub: "order-locked" },
        { label: "Available Now", value: "236",  sub: "free to sell" },
      ].map(c => (
        <div key={c.label} className="bg-neutral-900 border border-neutral-800 rounded-xl p-5">
          <p className="text-xs font-semibold text-neutral-500 uppercase tracking-wider mb-2">{c.label}</p>
          <p className="text-3xl font-bold text-white">{c.value}</p>
          <p className="text-xs text-neutral-600 mt-1">{c.sub}</p>
        </div>
      ))}
    </div>
  );
}

function ImmutableLedgerViewer() {
  return (
    <div className="bg-neutral-900 border border-neutral-800 rounded-xl overflow-hidden">
      <div className="p-4 border-b border-neutral-800 flex justify-between items-center">
        <div>
          <h2 className="text-sm font-semibold text-white flex items-center gap-2">
            Immutable Inventory Ledger
            <span className="text-[9px] px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 uppercase font-bold">
              Append-Only
            </span>
          </h2>
          <p className="text-xs text-neutral-600 mt-0.5">Every stock movement. Permanent. Auditable. No UPDATEs.</p>
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-neutral-800">
              {["Movement", "Product", "Qty", "Reason", "Severity", "Correlation", "When"].map(h => (
                <th key={h} className="text-left px-4 py-3 text-xs font-semibold text-neutral-500 uppercase tracking-wide">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {mockLedgerEntries.map((e) => (
              <tr key={e.id} className="border-b border-neutral-800/50 hover:bg-neutral-800/30 transition-colors">
                <td className="px-4 py-3">
                  <span className={`font-mono font-semibold text-xs ${movementColor[e.movement_type]}`}>{e.movement_type}</span>
                </td>
                <td className="px-4 py-3 text-neutral-300 text-xs">{e.product}</td>
                <td className="px-4 py-3">
                  <span className={`font-bold text-sm ${e.qty < 0 ? "text-rose-400" : "text-emerald-400"}`}>
                    {e.qty > 0 ? `+${e.qty}` : e.qty}
                  </span>
                </td>
                <td className="px-4 py-3 text-xs text-neutral-400">{e.reason}</td>
                <td className="px-4 py-3"><SeverityBadge severity={e.severity} /></td>
                <td className="px-4 py-3 font-mono text-xs text-neutral-600">{e.correlation_id}</td>
                <td className="px-4 py-3 text-xs text-neutral-500">{e.at}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ReservationMonitor() {
  return (
    <div className="bg-neutral-900 border border-neutral-800 rounded-xl overflow-hidden">
      <div className="p-4 border-b border-neutral-800">
        <h2 className="text-sm font-semibold text-white">Active Reservations</h2>
      </div>
      <div className="flex flex-col divide-y divide-neutral-800">
        {mockReservations.map((r) => (
          <div key={r.id} className="px-4 py-3 flex items-center justify-between hover:bg-neutral-800/30">
            <div className="flex items-center gap-4">
              <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded border ${
                r.type === "HARD"
                  ? "bg-rose-500/10 text-rose-400 border-rose-500/20"
                  : "bg-blue-500/10 text-blue-400 border-blue-500/20"
              }`}>{r.type}</span>
              <div>
                <p className="text-sm text-neutral-200">{r.product} <span className="text-neutral-500">×{r.qty}</span></p>
                <p className="text-xs text-neutral-600 font-mono mt-0.5">{r.customer} · {r.correlation_id}</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-xs text-neutral-500">
                {r.type === "SOFT" ? `Expires in ${r.expires_in}` : "Hard Lock (Order Paid)"}
              </span>
              {r.type === "SOFT" && (
                <ActionableButton label="Release" icon="↑" variant="danger" />
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function DriftDetectionPanel() {
  return (
    <div className="bg-neutral-900 border border-rose-900/40 rounded-xl overflow-hidden">
      <div className="p-4 border-b border-rose-900/40 flex justify-between items-center">
        <h2 className="text-sm font-semibold text-white flex items-center gap-2">
          Drift Detection
          <SeverityBadge severity="CRITICAL" pulse />
        </h2>
        <span className="text-xs text-neutral-500">{mockDrifts.length} unresolved</span>
      </div>
      {mockDrifts.map((d) => (
        <div key={d.product} className="p-4 flex items-center justify-between">
          <div>
            <p className="text-sm font-semibold text-neutral-200">{d.product}</p>
            <p className="text-xs text-neutral-500 mt-1">
              Snapshot: <span className="text-amber-400">{d.snapshot}</span> · Ledger Calc: <span className="text-emerald-400">{d.ledger_calc}</span> · Delta: <span className="text-rose-400">+{d.delta}</span>
            </p>
            <p className="text-xs text-neutral-600 mt-0.5">Detected {d.detected_at}</p>
          </div>
          <div className="flex items-center gap-2">
            <ActionableButton label="Rebuild Snapshot" icon="⟳" variant="danger" />
            <ActionableButton label="Inspect Drift" icon="⬡" variant="ghost" />
          </div>
        </div>
      ))}
    </div>
  );
}

// ─────────────────────────────────────────────
// Page
// ─────────────────────────────────────────────
export default function InventoryConsolePage() {
  return (
    <div className="flex flex-col gap-6 p-8 min-h-screen bg-neutral-950 text-neutral-50 font-sans">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs text-neutral-500 mb-1">← Mission Control</p>
          <h1 className="text-2xl font-semibold text-white">Inventory Operations Console</h1>
        </div>
        <SeverityBadge severity="WARNING" />
      </div>

      <StockSummaryRow />
      <DriftDetectionPanel />
      <ImmutableLedgerViewer />
      <ReservationMonitor />
    </div>
  );
}
