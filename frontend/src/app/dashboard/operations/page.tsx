import React from "react";
import { MissionControlHeader } from "@/components/dashboard/mission-control-header";
import { OperationsGrid } from "@/components/dashboard/operations-grid";
import { LiveEventStream } from "@/components/dashboard/live-event-stream";

export default function OperationsDashboard() {
  return (
    <div className="flex flex-col gap-6 p-8 min-h-screen bg-neutral-950 text-neutral-50 font-sans">
      {/* HEADER SECTION */}
      <section>
        <MissionControlHeader />
      </section>

      {/* MAIN CONTENT GRID */}
      <section className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-full flex-grow">
        
        {/* Left Column: Operations Grid (2/3 width on large screens) */}
        <div className="lg:col-span-2 flex flex-col gap-6">
          <OperationsGrid />
        </div>

        {/* Right Column: Live Event Stream (1/3 width on large screens) */}
        <div className="h-[800px] border border-neutral-800 rounded-xl bg-neutral-900/50 backdrop-blur-sm overflow-hidden flex flex-col">
          <div className="p-4 border-b border-neutral-800 flex justify-between items-center bg-neutral-900">
            <h2 className="text-sm font-semibold tracking-wide text-neutral-400 uppercase flex items-center gap-2">
              <span className="relative flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
              </span>
              Live Event Stream
            </h2>
            <span className="text-xs text-neutral-500 font-mono">WebSocket Connected</span>
          </div>
          <div className="flex-grow overflow-hidden">
            <LiveEventStream />
          </div>
        </div>

      </section>
    </div>
  );
}
