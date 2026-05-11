import React from "react";

const gridCards = [
  {
    title: "Payment Operations",
    status: "HEALTHY",
    metrics: [
      { label: "Success Rate", value: "99.2%" },
      { label: "Webhook Retries", value: "3" },
      { label: "Pending Reconciliations", value: "0" }
    ]
  },
  {
    title: "Inventory Operations",
    status: "WARNING",
    metrics: [
      { label: "Drift Detected", value: "1", highlight: "text-amber-400" },
      { label: "Active Reservations", value: "45" },
      { label: "Rebuilds (24h)", value: "0" }
    ]
  },
  {
    title: "Connector Health",
    status: "HEALTHY",
    metrics: [
      { label: "Sync Uptime", value: "100%" },
      { label: "Throughput", value: "850 rec/m" },
      { label: "Schema Changes", value: "0" }
    ]
  },
  {
    title: "DLQ & Retries",
    status: "HEALTHY",
    metrics: [
      { label: "Dead Letters", value: "0" },
      { label: "Retry Success Rate", value: "95%" },
      { label: "Archived (30d)", value: "12" }
    ]
  }
];

export function OperationsGrid() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 h-full">
      {gridCards.map((card, idx) => (
        <div key={idx} className="bg-neutral-900 border border-neutral-800 rounded-xl p-5 flex flex-col justify-between hover:border-neutral-700 transition-colors">
          
          <div className="flex justify-between items-start mb-6">
            <h3 className="text-lg font-medium text-white">{card.title}</h3>
            <span className={`text-[10px] uppercase font-bold tracking-wider px-2 py-1 rounded-sm ${
              card.status === "HEALTHY" 
                ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" 
                : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
            }`}>
              {card.status}
            </span>
          </div>

          <div className="space-y-4">
            {card.metrics.map((m, i) => (
              <div key={i} className="flex justify-between items-end border-b border-neutral-800/50 pb-2 last:border-0 last:pb-0">
                <span className="text-sm text-neutral-400">{m.label}</span>
                <span className={`text-base font-semibold ${m.highlight || "text-neutral-100"}`}>
                  {m.value}
                </span>
              </div>
            ))}
          </div>

          <div className="mt-6 pt-4 border-t border-neutral-800">
            <button className="text-xs text-neutral-500 hover:text-white transition-colors flex items-center gap-1">
              Open Console <span>→</span>
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
