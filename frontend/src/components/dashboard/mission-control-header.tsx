import React from "react";

export function MissionControlHeader() {
  // En el futuro, estos datos vendrán de React Query (conectado a operational_confidence_engine)
  const confidenceScore = 98.7;
  const status = confidenceScore >= 98 ? "HEALTHY" : "WARNING";

  return (
    <div className="flex flex-col md:flex-row gap-4 items-center justify-between bg-neutral-900 border border-neutral-800 rounded-xl p-6">
      
      {/* Title & Status */}
      <div className="flex flex-col gap-1">
        <h1 className="text-2xl font-semibold tracking-tight text-white flex items-center gap-3">
          Mission Control
          <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            {status}
          </span>
        </h1>
        <p className="text-sm text-neutral-400">
          Operational visibility and system health monitoring
        </p>
      </div>

      {/* Primary Metrics */}
      <div className="flex items-center gap-8">
        
        {/* Metric 1: Operational Confidence Score (THE STAR) */}
        <div className="flex flex-col items-end border-r border-neutral-800 pr-8">
          <span className="text-xs font-semibold text-neutral-500 uppercase tracking-wider mb-1">
            Operational Confidence
          </span>
          <div className="flex items-baseline gap-2">
            <span className="text-4xl font-bold tracking-tighter text-white">
              {confidenceScore}
            </span>
            <span className="text-lg text-emerald-400 font-medium">%</span>
          </div>
        </div>

        {/* Metric 2: Revenue Realtime */}
        <div className="flex flex-col items-end border-r border-neutral-800 pr-8">
          <span className="text-xs font-semibold text-neutral-500 uppercase tracking-wider mb-1">
            Revenue (24h)
          </span>
          <div className="flex items-baseline gap-1">
            <span className="text-lg text-neutral-400 font-medium">$</span>
            <span className="text-3xl font-bold tracking-tight text-white">
              12,450
            </span>
          </div>
        </div>

        {/* Metric 3: Active Alerts */}
        <div className="flex flex-col items-end">
          <span className="text-xs font-semibold text-neutral-500 uppercase tracking-wider mb-1">
            Active Alerts
          </span>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold tracking-tight text-rose-500">
              2
            </span>
            <span className="text-sm text-neutral-400">critical</span>
          </div>
        </div>

      </div>
    </div>
  );
}
