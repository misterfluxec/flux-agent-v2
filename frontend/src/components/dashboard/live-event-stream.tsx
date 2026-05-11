import React from "react";

// Mock data representing incoming WebSocket events
const mockEvents = [
  {
    id: "evt_101",
    type: "inventory.drift_detected.v1",
    priority: "CRITICAL",
    time: "Just now",
    correlation_id: "corr_xyz987",
    payload: { snapshot: 5, ledger: 4 }
  },
  {
    id: "evt_102",
    type: "payment.completed.v1",
    priority: "HIGH",
    time: "2 min ago",
    correlation_id: "txn_abc123",
    payload: { amount: 150.00, gateway: "mercadopago" }
  },
  {
    id: "evt_103",
    type: "connector.sync.completed.v1",
    priority: "NORMAL",
    time: "5 min ago",
    correlation_id: "sync_job_44",
    payload: { records_processed: 1250 }
  },
  {
    id: "evt_104",
    type: "inventory.reserved.v1",
    priority: "LOW",
    time: "12 min ago",
    correlation_id: "txn_def456",
    payload: { item: "SKU-99", qty: 1 }
  }
];

const priorityConfig = {
  CRITICAL: { color: "text-rose-400", bg: "bg-rose-500/10", border: "border-rose-500/20" },
  HIGH: { color: "text-amber-400", bg: "bg-amber-500/10", border: "border-amber-500/20" },
  NORMAL: { color: "text-emerald-400", bg: "bg-emerald-500/10", border: "border-emerald-500/20" },
  LOW: { color: "text-neutral-400", bg: "bg-neutral-800/50", border: "border-neutral-800" }
};

export function LiveEventStream() {
  return (
    <div className="flex flex-col h-full overflow-y-auto custom-scrollbar p-2">
      <div className="flex flex-col gap-2">
        {mockEvents.map((event) => {
          const style = priorityConfig[event.priority as keyof typeof priorityConfig];
          return (
            <div 
              key={event.id}
              className={`p-3 rounded-lg border ${style.border} ${style.bg} hover:bg-neutral-800/80 transition-colors cursor-default`}
            >
              <div className="flex justify-between items-start mb-2">
                <span className={`text-xs font-bold uppercase tracking-wider ${style.color}`}>
                  {event.priority}
                </span>
                <span className="text-[10px] text-neutral-500 font-mono">
                  {event.time}
                </span>
              </div>
              
              <div className="text-sm font-medium text-neutral-200 mb-1 truncate">
                {event.type}
              </div>
              
              <div className="flex justify-between items-end mt-2">
                <div className="text-[10px] text-neutral-500 font-mono">
                  corr: {event.correlation_id}
                </div>
                <button className="text-[10px] text-neutral-400 hover:text-white underline decoration-neutral-600 underline-offset-2">
                  View Payload
                </button>
              </div>
            </div>
          );
        })}
      </div>
      
      {/* Ghosting effect for bottom */}
      <div className="mt-4 p-4 border border-dashed border-neutral-800 rounded-lg text-center">
        <span className="text-xs text-neutral-600 animate-pulse">Listening for events...</span>
      </div>
    </div>
  );
}
