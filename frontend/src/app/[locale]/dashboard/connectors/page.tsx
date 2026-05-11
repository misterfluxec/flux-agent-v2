'use client';

import React, { useState } from 'react';
import { ConnectorCards } from '@/components/connectors/ConnectorCards';
import { SyncTimeline } from '@/components/connectors/SyncTimeline';
import { MappingWizardPreview } from '@/components/connectors/MappingWizardPreview';
import { ConnectorMetrics } from '@/components/connectors/ConnectorMetrics';
import { Plus, Settings2, RefreshCw } from 'lucide-react';

export default function ConnectorsDashboard() {
  const [isWizardOpen, setIsWizardOpen] = useState(false);

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] overflow-hidden bg-slate-950 text-slate-200">
      
      {/* HEADER KPI BAR */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-white/5 bg-slate-900/40 backdrop-blur-md z-10">
        <div>
          <h1 className="text-xl font-bold bg-gradient-to-r from-slate-100 to-slate-400 bg-clip-text text-transparent">
            Connected Operations
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Supervisa e integra tus ERPs en tiempo real.
          </p>
        </div>

        <div className="flex items-center gap-4">
          <ConnectorMetrics />
          
          <button 
            onClick={() => setIsWizardOpen(true)}
            className="flex items-center gap-2 bg-indigo-500 hover:bg-indigo-400 transition-colors text-white text-sm font-medium px-4 py-2 rounded-lg shadow-lg shadow-indigo-500/20"
          >
            <Plus className="w-4 h-4" />
            Nuevo Conector
          </button>
        </div>
      </div>

      {/* MAIN CONTENT AREA */}
      <div className="flex-1 flex overflow-hidden">
        
        {/* COLUMN 1: CONNECTOR CARDS & ALERTS */}
        <div className="w-full lg:w-[65%] flex flex-col border-r border-white/5 overflow-y-auto">
          <div className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold tracking-wider text-slate-400 uppercase">Integraciones Activas</h2>
              <button className="text-slate-500 hover:text-slate-300 transition-colors p-1">
                <Settings2 className="w-4 h-4" />
              </button>
            </div>
            
            {/* Cards Grid */}
            <ConnectorCards />
            
          </div>
        </div>

        {/* COLUMN 2: SYNC TIMELINE & DLQ */}
        <div className="hidden lg:flex w-[35%] flex-col bg-slate-900/20 relative">
          <div className="p-4 border-b border-white/5 bg-slate-900/30 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-slate-300">Live Sync Timeline</h2>
            <div className="flex items-center gap-2">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-60" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
              </span>
              <span className="text-[10px] text-emerald-500/80 uppercase tracking-wider font-bold">Listening</span>
            </div>
          </div>
          
          <div className="flex-1 overflow-hidden">
            <SyncTimeline />
          </div>
        </div>

      </div>

      {/* MAPPING WIZARD OVERLAY */}
      {isWizardOpen && (
        <MappingWizardPreview onClose={() => setIsWizardOpen(false)} />
      )}
      
    </div>
  );
}
