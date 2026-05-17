'use client';

import { useState, useEffect, useCallback } from 'react';
import { useConversations } from '@/hooks/useConversations';
import { ConversationsList } from '@/components/conversations/ConversationsList';
import { ChatWindow } from '@/components/conversations/ChatWindow';
import { LeadIntelligence } from '@/components/conversations/LeadIntelligence';
import {
  MessageSquare, Flame, User, LayoutGrid,
  AlertTriangle, Users, ArrowRight, Phone, Mail, TrendingUp,
  ChevronRight, RefreshCw, Search, Filter,
} from 'lucide-react';
import { useEventBus } from '@/providers/EventBusProvider';
import { fetchLeads, LeadData } from '@/lib/api';
import { toast } from 'sonner';

// =============================================================================
// PIPELINE STAGES (for CRM tab)
// =============================================================================

const statusColors: Record<string, string> = {
  nuevo: "text-blue-400 bg-blue-500/10 border-blue-500/20",
  contactado: "text-amber-400 bg-amber-500/10 border-amber-500/20",
  interesado: "text-purple-400 bg-purple-500/10 border-purple-500/20",
  cerrado: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
  perdido: "text-rose-400 bg-rose-500/10 border-rose-500/20",
};
const pipelineStages = ["nuevo", "contactado", "interesado", "cerrado"];

// =============================================================================
// MAIN PAGE — 4 Capas Cognitivas
// =============================================================================

type ViewTab = "all" | "hot" | "human" | "pipeline";

export default function OperationsPage() {
  const {
    conversations, selected, selectedId, setSelectedId,
    search, setSearch, statusFilter, setStatusFilter,
    sendMessage, isSending,
  } = useConversations();

  const { history } = useEventBus();
  const [activeTab, setActiveTab] = useState<ViewTab>("all");

  // Derived priority counts from EventBus + conversations
  const handoffCount = conversations.filter(c => c.status === 'waiting').length;
  const hotCount = conversations.filter(c => c.leadScore >= 70).length;
  const humanCount = conversations.filter(c => c.status === 'waiting').length;

  const handleTakeover = () => {
    if (!selectedId) return;
    toast.success(`Control transferido. Yanua pausada para este lead.`);
  };

  const TABS = [
    { id: "all" as const, label: "Todos", icon: MessageSquare, count: conversations.length },
    { id: "hot" as const, label: "Calientes", icon: Flame, count: hotCount },
    { id: "human" as const, label: "Humanos", icon: User, count: humanCount },
    { id: "pipeline" as const, label: "Pipeline", icon: LayoutGrid, count: null },
  ];

  return (
    <div className="flex flex-col h-[calc(100vh-3rem)] overflow-hidden">

      {/* ═══ CAPA 1: PRIORIDAD VIVA ═══ */}
      <PriorityBar
        handoffs={handoffCount}
        hotLeads={hotCount}
        totalActive={conversations.filter(c => c.status === 'active').length}
        eventsToday={history.length}
      />

      {/* ═══ TABS ═══ */}
      <div className="flex items-center gap-1 px-4 py-2 border-b border-white/5 bg-black/40 shrink-0">
        {TABS.map(tab => {
          const Icon = tab.icon;
          const active = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[13px] font-semibold transition-all ${
                active
                  ? "bg-cyan-500/[0.08] text-cyan-300/90 border border-cyan-500/[0.12]"
                  // Inactivo: slate-400 en vez de white/30 — más legible, menos fa tigante
                  : "text-slate-400 hover:text-slate-200 hover:bg-white/[0.03] border border-transparent"
              }`}
            >
              <Icon className="h-3.5 w-3.5" />
              {tab.label}
              {tab.count !== null && tab.count > 0 && (
                <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-bold ${
                  active ? "bg-cyan-500/20 text-cyan-300" :
                  tab.id === "hot" && tab.count > 0 ? "bg-orange-500/20 text-orange-400" :
                  tab.id === "human" && tab.count > 0 ? "bg-red-500/20 text-red-400" :
                  "bg-white/5 text-white/30"
                }`}>
                  {tab.count}
                </span>
              )}
            </button>
          );
        })}

        {/* Breadcrumb path — muy discreto */}
        <div className="ml-auto flex items-center gap-1.5 text-[11px] text-slate-600 font-medium">
          Yanua <ChevronRight className="w-3 h-3" /> Operaciones
        </div>
      </div>

      {/* ═══ CAPAS 2+3+4: INBOX + CONTEXTO + ACCIONES ═══ */}
      {activeTab === "pipeline" ? (
        <PipelineView />
      ) : (
        <div className="flex-1 flex overflow-hidden">
          {/* Capa 2: Inbox Operacional */}
          <ConversationsList
            conversations={conversations}
            selectedId={selectedId}
            onSelect={setSelectedId}
            search={search}
            onSearchChange={setSearch}
            statusFilter={statusFilter}
            onStatusFilterChange={setStatusFilter}
          />

          {/* Capa 3: Chat */}
          <div className="flex-1 flex flex-col min-w-0">
            <ChatWindow conversation={selected} onSend={sendMessage} isSending={isSending} />
          </div>

          {/* Capa 4: Contexto IA + Acciones */}
          <LeadIntelligence conversation={selected} onTakeover={handleTakeover} />
        </div>
      )}
    </div>
  );
}

// =============================================================================
// CAPA 1 — PRIORITY BAR (Prioridad Viva)
// =============================================================================

function PriorityBar({ handoffs, hotLeads, totalActive, eventsToday }: {
  handoffs: number; hotLeads: number; totalActive: number; eventsToday: number;
}) {
  const items = [
    handoffs > 0 && { icon: User, text: `${handoffs} handoff${handoffs > 1 ? "s" : ""} pendiente${handoffs > 1 ? "s" : ""}`, color: "text-red-400 bg-red-500/10" },
    hotLeads > 0 && { icon: Flame, text: `${hotLeads} lead${hotLeads > 1 ? "s" : ""} caliente${hotLeads > 1 ? "s" : ""}`, color: "text-orange-400 bg-orange-500/10" },
    totalActive > 0 && { icon: MessageSquare, text: `${totalActive} conversación${totalActive > 1 ? "es" : ""} activa${totalActive > 1 ? "s" : ""}`, color: "text-cyan-400 bg-cyan-500/10" },
    eventsToday > 0 && { icon: AlertTriangle, text: `${eventsToday} evento${eventsToday > 1 ? "s" : ""} hoy`, color: "text-white/30 bg-white/5" },
  ].filter(Boolean) as { icon: any; text: string; color: string }[];

  if (items.length === 0) return null;

  return (
    // Priority bar: solo aparece cuando hay items de priority (PriorityBar ya filtro)
    <div className="flex items-center gap-2 px-4 py-2 border-b border-white/[0.04] bg-black/30 shrink-0 overflow-x-auto">
      {items.map((item, i) => {
        const Icon = item.icon;
        return (
          <div key={i} className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[12px] font-semibold whitespace-nowrap ${item.color}`}>
            <Icon className="h-3 w-3" />
            {item.text}
          </div>
        );
      })}
    </div>
  );
}

// =============================================================================
// PIPELINE VIEW — Kanban (absorbed from CRM)
// =============================================================================

function PipelineView() {
  const [leads, setLeads] = useState<LeadData[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");

  const loadLeads = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchLeads();
      setLeads(data);
    } catch { /* silent */ } finally { setLoading(false); }
  }, []);

  useEffect(() => { loadLeads(); }, [loadLeads]);

  const filtered = leads.filter(l =>
    l.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    l.phone.includes(searchTerm) ||
    l.email.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const stats = {
    total: leads.length,
    cerrados: leads.filter(l => l.status === "cerrado").length,
    ingresos: leads.filter(l => l.status === "cerrado").reduce((s, l) => s + l.monto, 0),
  };

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      {/* Stats + Filters */}
      <div className="px-5 py-4 border-b border-white/5 shrink-0 space-y-3">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Users className="h-4 w-4 text-white/20" />
            <span className="text-xs font-bold text-white/40">{stats.total} leads</span>
          </div>
          <div className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-emerald-400/50" />
            <span className="text-xs font-bold text-emerald-400/70">{stats.cerrados} cerrados · ${stats.ingresos.toLocaleString()}</span>
          </div>
          <div className="ml-auto">
            <button onClick={loadLeads} disabled={loading}
              className="text-[10px] font-bold text-white/20 hover:text-white/50 flex items-center gap-1">
              <RefreshCw className={`h-3 w-3 ${loading ? "animate-spin" : ""}`} /> Sincronizar
            </button>
          </div>
        </div>
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-white/20" />
          <input value={searchTerm} onChange={e => setSearchTerm(e.target.value)} placeholder="Buscar lead..."
            className="w-full bg-white/5 border border-white/5 rounded-lg pl-9 pr-4 py-2 text-xs text-white placeholder:text-white/20 focus:outline-none focus:border-cyan-500/30" />
        </div>
      </div>

      {/* Kanban Columns */}
      <div className="flex-1 flex gap-3 overflow-x-auto p-4">
        {pipelineStages.map(stage => {
          const stageLeads = filtered.filter(l => l.status === stage);
          return (
            <div key={stage} className="flex-none w-72 bg-white/[0.02] border border-white/5 rounded-2xl p-3 flex flex-col">
              <div className="flex items-center justify-between mb-3 px-1">
                <h3 className="text-xs font-bold text-white/50 capitalize flex items-center gap-2">
                  <div className={`w-2 h-2 rounded-full ${statusColors[stage]?.split(' ')[1] || 'bg-white/20'}`} />
                  {stage}
                </h3>
                <span className="text-[10px] font-bold text-white/20 bg-white/5 px-1.5 py-0.5 rounded">{stageLeads.length}</span>
              </div>
              <div className="flex-1 overflow-y-auto space-y-2 pr-1" style={{ scrollbarWidth: 'thin', scrollbarColor: 'rgba(255,255,255,0.1) transparent' }}>
                {stageLeads.length === 0 ? (
                  <div className="h-20 border-2 border-dashed border-white/5 rounded-xl flex items-center justify-center text-[10px] text-white/15">
                    Sin leads
                  </div>
                ) : (
                  stageLeads.map(lead => (
                    <div key={lead.id} className="bg-black/40 border border-white/5 rounded-xl p-3 hover:border-white/10 transition-colors cursor-pointer group">
                      <div className="flex justify-between items-start mb-1.5">
                        <h4 className="text-xs font-bold text-white/70 truncate pr-2">{lead.name}</h4>
                        <span className="text-[10px] font-bold text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded shrink-0">
                          ${lead.monto}
                        </span>
                      </div>
                      <div className="space-y-0.5 mb-2">
                        {lead.phone && <div className="flex items-center gap-1.5 text-[10px] text-white/25"><Phone className="w-2.5 h-2.5" />{lead.phone}</div>}
                        {lead.email && <div className="flex items-center gap-1.5 text-[10px] text-white/25"><Mail className="w-2.5 h-2.5" />{lead.email}</div>}
                      </div>
                      <div className="flex items-center justify-between pt-2 border-t border-white/5">
                        <span className="text-[9px] text-white/15 bg-white/5 px-1.5 py-0.5 rounded uppercase tracking-wider">{lead.canal}</span>
                        <ArrowRight className="w-3 h-3 text-white/10 opacity-0 group-hover:opacity-100 transition-opacity" />
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
