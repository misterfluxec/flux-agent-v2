import React from "react";
import { SeverityBadge } from "@/components/ui/severity-badge";
import { ActionableButton } from "@/components/ui/actionable-button";
import type { Severity } from "@/components/ui/severity-badge";

// ─────────────────────────────────────────────
// Mock Data
// ─────────────────────────────────────────────
type DLQStatus = "dlq" | "retrying" | "archived";

const mockDLQEvents = [
  {
    id: "dlq_001",
    event_type: "payment.webhook.ingest",
    version: "v1",
    status: "dlq" as DLQStatus,
    severity: "CRITICAL" as Severity,
    error_reason: "Database connection timeout during idempotency check.",
    retry_count: 5,
    last_attempt: "3 min ago",
    first_failed: "22 min ago",
    correlation_id: "txn_def456",
    replayable: true,
    payload_preview: `{ "type": "payment.updated", "data": { "id": 12345 } }`,
  },
  {
    id: "dlq_002",
    event_type: "inventory.expiration_worker",
    version: "v1",
    status: "dlq" as DLQStatus,
    severity: "HIGH" as Severity,
    error_reason: "Deadlock detected on inventory_locks table. SKIP LOCKED failed.",
    retry_count: 3,
    last_attempt: "15 min ago",
    first_failed: "1 hr ago",
    correlation_id: "corr_exp_009",
    replayable: true,
    payload_preview: `{ "reservation_id": "res_07", "product_id": "prod_11" }`,
  },
  {
    id: "dlq_003",
    event_type: "connector.schema_changed",
    version: "v1",
    status: "archived" as DLQStatus,
    severity: "WARNING" as Severity,
    error_reason: "Schema drift detected. Marked as non-replayable by Event Registry policy.",
    retry_count: 0,
    last_attempt: "—",
    first_failed: "2 days ago",
    correlation_id: "sync_job_44",
    replayable: false,
    payload_preview: `{ "connector": "google_sheets", "changed_columns": ["price"] }`,
  },
];

const statusStyles: Record<DLQStatus, string> = {
  dlq:      "bg-rose-500/10 text-rose-400 border-rose-500/20",
  retrying: "bg-amber-500/10 text-amber-400 border-amber-500/20",
  archived: "bg-neutral-800 text-neutral-500 border-neutral-700",
};

// ─────────────────────────────────────────────
// Sub-components
// ─────────────────────────────────────────────
function RetryRecoveryStats() {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {[
        { label: "Dead Letters (active)", value: "2", highlight: "text-rose-400" },
        { label: "Retry Success Rate",    value: "88%",  highlight: "text-emerald-400" },
        { label: "Avg. Retries to Heal",  value: "2.1",  highlight: "text-white" },
        { label: "Archived (30d)",        value: "12",   highlight: "text-neutral-400" },
      ].map(c => (
        <div key={c.label} className="bg-neutral-900 border border-neutral-800 rounded-xl p-5">
          <p className="text-xs font-semibold text-neutral-500 uppercase tracking-wider mb-2">{c.label}</p>
          <p className={`text-3xl font-bold tracking-tight ${c.highlight}`}>{c.value}</p>
        </div>
      ))}
    </div>
  );
}

function PayloadPreview({ payload }: { payload: string }) {
  return (
    <pre className="mt-2 p-2 rounded-md bg-neutral-950 border border-neutral-800 text-[10px] font-mono text-neutral-500 overflow-x-auto whitespace-pre-wrap">
      {payload}
    </pre>
  );
}

function DLQTable() {
  const [expanded, setExpanded] = React.useState<string | null>(null);

  return (
    <div className="bg-neutral-900 border border-neutral-800 rounded-xl overflow-hidden">
      <div className="p-4 border-b border-neutral-800 flex justify-between items-center">
        <h2 className="text-sm font-semibold text-white">Dead Letter Queue</h2>
        <span className="text-xs text-neutral-500 font-mono">{mockDLQEvents.length} total events</span>
      </div>

      <div className="flex flex-col divide-y divide-neutral-800">
        {mockDLQEvents.map((evt) => (
          <div key={evt.id} className="px-5 py-4 hover:bg-neutral-800/20 transition-colors">
            {/* Row header */}
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                {/* Event type + badges */}
                <div className="flex items-center flex-wrap gap-2 mb-2">
                  <span className="font-mono text-sm font-semibold text-neutral-200">
                    {evt.event_type}
                    <span className="text-neutral-600">.{evt.version}</span>
                  </span>
                  <span className={`text-[9px] uppercase font-bold px-1.5 py-0.5 rounded border ${statusStyles[evt.status]}`}>
                    {evt.status}
                  </span>
                  <SeverityBadge severity={evt.severity} pulse={evt.status === "dlq" && evt.severity === "CRITICAL"} />
                  {!evt.replayable && (
                    <span className="text-[9px] uppercase px-1.5 py-0.5 rounded bg-neutral-800 text-neutral-600 border border-neutral-700">
                      NON-REPLAYABLE
                    </span>
                  )}
                </div>

                {/* Failure reason */}
                <p className="text-xs text-rose-300/80 mb-2">
                  <span className="text-neutral-600">Reason: </span>{evt.error_reason}
                </p>

                {/* Meta row */}
                <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[10px] text-neutral-600 font-mono">
                  <span>corr: {evt.correlation_id}</span>
                  <span>retries: <span className="text-neutral-400">{evt.retry_count}</span></span>
                  <span>last attempt: <span className="text-neutral-400">{evt.last_attempt}</span></span>
                  <span>first failed: <span className="text-neutral-400">{evt.first_failed}</span></span>
                </div>

                {/* Payload preview (expandable) */}
                {expanded === evt.id && <PayloadPreview payload={evt.payload_preview} />}
              </div>

              {/* Actions */}
              <div className="flex flex-col items-end gap-2 flex-shrink-0">
                {evt.replayable && evt.status === "dlq" && (
                  <ActionableButton label="Replay" icon="↻" />
                )}
                {evt.status === "dlq" && (
                  <ActionableButton label="Archive" icon="⊡" variant="danger" />
                )}
                <ActionableButton
                  label={expanded === evt.id ? "Hide Payload" : "View Payload"}
                  icon="{ }"
                  variant="ghost"
                  onClick={() => setExpanded(expanded === evt.id ? null : evt.id)}
                />
              </div>
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
export default function RetryCenterPage() {
  return (
    <div className="flex flex-col gap-6 p-8 min-h-screen bg-neutral-950 text-neutral-50 font-sans">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs text-neutral-500 mb-1">← Mission Control / System</p>
          <h1 className="text-2xl font-semibold text-white">DLQ & Retry Center</h1>
          <p className="text-xs text-neutral-500 mt-1">
            Every failed event is here. Nothing gets lost.
          </p>
        </div>
        <SeverityBadge severity="CRITICAL" pulse />
      </div>

      <RetryRecoveryStats />
      <DLQTable />
    </div>
  );
}
