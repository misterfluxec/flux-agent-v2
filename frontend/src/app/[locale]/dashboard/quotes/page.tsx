'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getQuotes, approveQuote, convertQuoteToOrder, Quote } from '@/services/api/commerce';
import {
  FileText, Clock, CheckCircle2, XCircle, AlertTriangle,
  Loader2, ArrowRight, Eye, Send, Filter
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';

// ─── STATUS CONFIG ───────────────────────────────────────────────────────
const STATUS_CONFIG: Record<string, { label: string; icon: any; color: string }> = {
  draft:    { label: 'Borrador',  icon: FileText,       color: 'bg-slate-500/10 text-slate-400 border-slate-500/20' },
  sent:     { label: 'Enviada',   icon: Send,           color: 'bg-blue-500/10 text-blue-400 border-blue-500/20' },
  accepted: { label: 'Aceptada',  icon: CheckCircle2,   color: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' },
  rejected: { label: 'Rechazada', icon: XCircle,        color: 'bg-red-500/10 text-red-400 border-red-500/20' },
  expired:  { label: 'Expirada',  icon: AlertTriangle,  color: 'bg-amber-500/10 text-amber-400 border-amber-500/20' },
};

export default function QuotesPage() {
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState<string>('all');

  const { data: quotes = [], isLoading } = useQuery({
    queryKey: ['quotes'],
    queryFn: () => getQuotes(),
  });

  const approveMutation = useMutation({
    mutationFn: (id: string) => approveQuote(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['quotes'] });
      toast.success('Cotización aprobada — lista para convertir a sort_order');
    },
    onError: () => toast.error('Error al aprobar cotización'),
  });

  const convertMutation = useMutation({
    mutationFn: (id: string) => convertQuoteToOrder(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['quotes'] });
      queryClient.invalidateQueries({ queryKey: ['orders'] });
      toast.success('✅ Orden creada exitosamente desde cotización');
    },
    onError: () => toast.error('Error al convertir cotización'),
  });

  const filtered = statusFilter === 'all' ? quotes : quotes.filter((q: Quote) => q.status === statusFilter);

  // Summary counts
  const counts = {
    all: quotes.length,
    draft: quotes.filter((q: Quote) => q.status === 'draft').length,
    sent: quotes.filter((q: Quote) => q.status === 'sent').length,
    accepted: quotes.filter((q: Quote) => q.status === 'accepted').length,
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-500 pb-12 px-6 md:px-8 max-w-6xl mx-auto pt-6">

      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <FileText className="w-4 h-4 text-cyan-400" />
          <span className="text-[10px] font-bold uppercase tracking-widest text-cyan-400/80">Cotizaciones</span>
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-white/80">
          Cotizaciones Comerciales
        </h1>
        <p className="text-sm text-white/40 mt-1">
          Proformas generadas por la IA — revisa, aprueba y convierte a órdenes
        </p>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1">
        {[
          { key: 'all', label: 'Todas', count: counts.all },
          { key: 'draft', label: 'Borradores', count: counts.draft },
          { key: 'sent', label: 'Enviadas', count: counts.sent },
          { key: 'accepted', label: 'Aceptadas', count: counts.accepted },
        ].map(tab => (
          <button
            key={tab.key}
            onClick={() => setStatusFilter(tab.key)}
            className={`px-4 py-2 text-xs font-bold rounded-xl border transition-all ${
              statusFilter === tab.key
                ? 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20'
                : 'bg-white/[0.02] text-white/40 border-white/[0.05] hover:border-white/10'
            }`}
          >
            {tab.label} <span className="ml-1.5 opacity-60">{tab.count}</span>
          </button>
        ))}
      </div>

      {/* Quotes List */}
      <div className="space-y-3">
        {isLoading ? (
          <div className="bg-[#111827] border border-white/5 rounded-2xl p-12 text-center">
            <Loader2 className="w-5 h-5 animate-spin mx-auto mb-2 text-white/30" />
            <p className="text-sm text-white/30">Cargando cotizaciones...</p>
          </div>
        ) : filtered.length === 0 ? (
          <div className="bg-[#111827] border border-white/5 rounded-2xl p-12 text-center">
            <FileText className="w-8 h-8 text-white/10 mx-auto mb-3" />
            <p className="text-sm font-semibold text-white/40">No hay cotizaciones</p>
            <p className="text-xs text-white/20 mt-1">
              Las cotizaciones se generan automáticamente cuando un agente IA identifica una oportunidad de venta
            </p>
          </div>
        ) : (
          filtered.map((quote: Quote) => {
            const config = STATUS_CONFIG[quote.status] || STATUS_CONFIG.draft;
            const StatusIcon = config.icon;
            const validUntil = quote.valid_until ? new Date(quote.valid_until) : null;
            const isExpiringSoon = validUntil && (validUntil.getTime() - Date.now()) < 48 * 60 * 60 * 1000;

            return (
              <div
                key={quote.id}
                className="bg-[#111827] border border-white/5 rounded-2xl p-5 hover:border-white/10 transition-all group"
              >
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                  {/* Left: Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="text-xs font-mono text-white/30">#{quote.id.slice(0, 8)}</span>
                      <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 text-[10px] font-bold rounded-lg border ${config.color}`}>
                        <StatusIcon className="w-3 h-3" />
                        {config.label}
                      </span>
                      {isExpiringSoon && quote.status === 'sent' && (
                        <span className="text-[10px] font-bold text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded-md border border-amber-500/20">
                          ⏰ Expira pronto
                        </span>
                      )}
                    </div>

                    <div className="flex items-baseline gap-4">
                      <p className="text-xl font-black text-white/90 tabular-nums">
                        ${quote.total.toFixed(2)}
                      </p>
                      <p className="text-xs text-white/30">
                        {quote.items?.length || 0} ítem{(quote.items?.length || 0) !== 1 ? 's' : ''}
                      </p>
                    </div>

                    <div className="flex items-center gap-4 mt-2 text-[11px] text-white/25">
                      <span>Cliente: {quote.customer_id?.slice(0, 12)}...</span>
                      <span>Creada: {new Date(quote.created_at).toLocaleDateString()}</span>
                      {validUntil && <span>Válida hasta: {validUntil.toLocaleDateString()}</span>}
                    </div>
                  </div>

                  {/* Right: Actions — Human-in-the-Loop */}
                  <div className="flex items-center gap-2 shrink-0">
                    {/* DRAFT → Aprobar (HITL) */}
                    {quote.status === 'draft' && (
                      <Button
                        size="sm"
                        onClick={() => approveMutation.mutate(quote.id)}
                        disabled={approveMutation.isPending}
                        className="h-9 px-4 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-bold shadow-[0_0_12px_rgba(16,185,129,0.2)]"
                      >
                        {approveMutation.isPending ? (
                          <Loader2 className="w-3.5 h-3.5 animate-spin mr-1.5" />
                        ) : (
                          <CheckCircle2 className="w-3.5 h-3.5 mr-1.5" />
                        )}
                        Aprobar
                      </Button>
                    )}

                    {/* ACCEPTED → Convertir a Orden */}
                    {quote.status === 'accepted' && (
                      <Button
                        size="sm"
                        onClick={() => convertMutation.mutate(quote.id)}
                        disabled={convertMutation.isPending}
                        className="h-9 px-4 bg-cyan-600 hover:bg-cyan-500 text-white rounded-xl text-xs font-bold shadow-[0_0_12px_rgba(6,182,212,0.2)]"
                      >
                        {convertMutation.isPending ? (
                          <Loader2 className="w-3.5 h-3.5 animate-spin mr-1.5" />
                        ) : (
                          <ArrowRight className="w-3.5 h-3.5 mr-1.5" />
                        )}
                        Crear Orden
                      </Button>
                    )}

                    {/* Ver detalles */}
                    <Button
                      size="icon"
                      variant="ghost"
                      className="h-9 w-9 text-white/20 hover:text-white/50 rounded-xl"
                    >
                      <Eye className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
