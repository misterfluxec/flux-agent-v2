'use client';

import React, { useState } from 'react';
import { ConnectorCards } from '@/components/connectors/ConnectorCards';
import { SyncTimeline } from '@/components/connectors/SyncTimeline';
import { ConnectorWizard } from '@/components/connectors/ConnectorWizard';
import { ConnectorMetrics } from '@/components/connectors/ConnectorMetrics';
import { Plus, Settings2 } from 'lucide-react';

export default function IntegrationsDashboard() {
  const [isWizardOpen, setIsWizardOpen] = useState(false);

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] overflow-hidden bg-slate-950 text-slate-200">
      
      {/* HEADER KPI BAR */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-white/5 bg-slate-900/40 backdrop-blur-md z-10">
        <div>
          <h1 className="text-xl font-bold bg-gradient-to-r from-emerald-100 to-emerald-400 bg-clip-text text-transparent">
            Integraciones Operacionales
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Sincroniza tus ERPs, Bases de Datos, CRMs e Importa archivos estructurados (Excel/CSV).
          </p>
        </div>

        <div className="flex items-center gap-4">
          <ConnectorMetrics />
          
          <button 
            onClick={() => setIsWizardOpen(true)}
            className="flex items-center gap-2 bg-emerald-500/20 hover:bg-emerald-500/30 border border-emerald-500/50 transition-colors text-emerald-400 text-sm font-bold px-4 py-2 rounded-lg"
          >
            <Plus className="w-4 h-4" />
            Conectar Sistema
          </button>
        </div>
      </div>

      {/* MAIN CONTENT AREA */}
      <div className="flex-1 flex overflow-hidden">
        
        {/* COLUMN 1: CONNECTOR CARDS & ALERTS */}
        <div className="w-full lg:w-[65%] flex flex-col border-r border-white/5 overflow-y-auto">
          <div className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold tracking-wider text-slate-400 uppercase">Fuentes Operacionales e Importaciones</h2>
              <button className="text-slate-500 hover:text-slate-300 transition-colors p-1">
                <Settings2 className="w-4 h-4" />
              </button>
            </div>

            {/* Architecture Flow Visualization */}
            <div className="mb-6 p-4 rounded-xl border border-white/5 bg-slate-900/50 hidden md:block">
              <div className="flex items-center justify-between text-[10px] font-mono text-slate-500 uppercase tracking-widest text-center">
                <div className="flex-1">Source<br/><span className="text-slate-300 font-bold">ERP / Sheets</span></div>
                <div className="text-emerald-500/50">→</div>
                <div className="flex-1">Engine<br/><span className="text-emerald-400 font-bold">Connector</span></div>
                <div className="text-emerald-500/50">→</div>
                <div className="flex-1">Process<br/><span className="text-slate-300 font-bold">Normalization</span></div>
                <div className="text-emerald-500/50">→</div>
                <div className="flex-1">Destination<br/><span className="text-emerald-400 font-bold">Catalog / Orders</span></div>
              </div>
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
        <ConnectorWizard onClose={() => setIsWizardOpen(false)} />
      )}
      
    </div>
  );
}
