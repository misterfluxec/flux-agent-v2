'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { MessageSquare, Users, Zap, Bot, ArrowRight, Sparkles, Plus, Terminal, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface StatsOverview {
  kpis: {
    total_conversaciones: number;
    leads_capturados: number;
    uso_tokens: number;
  };
}

export default function DashboardPage() {
  const router = useRouter();
  const [stats, setStats] = useState<StatsOverview | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchStats() {
      try {
        const token = localStorage.getItem('flux_token');
        if (!token) {
          router.push('/login');
          return;
        }

        const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:9000";
        const res = await fetch(`${BACKEND_URL}/api/v1/analytics/overview`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (res.ok) {
          const data = await res.json();
          setStats({
            kpis: {
              total_conversaciones: data.total_conversations || 0,
              leads_capturados: data.total_messages || 0,
              uso_tokens: data.uso_tokens || 0,
            }
          });
        }
      } catch (error) {
        console.error("Error fetching stats:", error);
      } finally {
        setLoading(false);
      }
    }

    fetchStats();
  }, [router]);

  return (
    <div className="space-y-8 animate-in fade-in duration-500 pb-12">
      {/* HEADER & YANUA COPILOT */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">Inicio</h1>
          <p className="text-muted-foreground mt-1">Centro de operaciones de tu IA comercial.</p>
        </div>
        <div className="flex gap-3">
          <Button variant="outline" className="border-border hover:bg-white/5 gap-2">
            <RefreshCw className="w-4 h-4" />
            Sincronizar Datos
          </Button>
          <Button onClick={() => router.push('/dashboard/agent')} className="bg-primary text-primary-foreground hover:bg-primary-hover gap-2 shadow-[0_0_15px_rgba(6,182,212,0.3)]">
            <Plus className="w-4 h-4" />
            Nuevo Agente
          </Button>
        </div>
      </div>

      {/* YANUA COPILOT BANNER */}
      <div className="relative overflow-hidden rounded-2xl border border-primary/20 bg-card p-6 md:p-8 shadow-lg group">
        <div className="absolute top-0 right-0 w-64 h-64 bg-primary/10 rounded-full blur-3xl -mr-16 -mt-16 pointer-events-none transition-all group-hover:bg-primary/20"></div>
        <div className="relative z-10 flex flex-col md:flex-row items-center gap-6">
          <div className="w-16 h-16 rounded-full bg-primary/20 border border-primary/30 flex items-center justify-center flex-shrink-0 shadow-[0_0_20px_rgba(6,182,212,0.4)]">
            <Bot className="w-8 h-8 text-primary" />
          </div>
          <div className="flex-1 text-center md:text-left">
            <div className="flex items-center justify-center md:justify-start gap-2 mb-1">
              <h2 className="text-xl font-bold text-foreground">Hola, soy Yanua ✨</h2>
            </div>
            <p className="text-muted-foreground text-sm md:text-base max-w-2xl">
              Tu sistema está operando correctamente. He detectado 3 conversaciones nuevas en WhatsApp que requieren atención humana, y 12 productos que fueron consultados sin éxito en la base de conocimientos.
            </p>
          </div>
          <div className="flex-shrink-0">
            <Button className="bg-white/5 hover:bg-white/10 text-foreground border border-white/10 gap-2">
              <Sparkles className="w-4 h-4 text-primary" />
              Ver Insights
            </Button>
          </div>
        </div>
      </div>

      {/* QUICK ACTIONS */}
      <div>
        <h3 className="text-sm font-semibold text-muted-foreground mb-4 uppercase tracking-wider">Acciones Rápidas</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div onClick={() => router.push('/dashboard/agent')} className="p-4 rounded-xl border border-border bg-card hover:bg-white/5 hover:border-white/20 transition cursor-pointer group flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-primary/10 rounded-lg text-primary"><Bot className="w-5 h-5" /></div>
              <span className="font-medium text-sm">Afinar Personalidad</span>
            </div>
            <ArrowRight className="w-4 h-4 text-muted-foreground group-hover:text-primary transition-colors" />
          </div>
          <div onClick={() => router.push('/dashboard/data')} className="p-4 rounded-xl border border-border bg-card hover:bg-white/5 hover:border-white/20 transition cursor-pointer group flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-500/10 rounded-lg text-blue-500"><Terminal className="w-5 h-5" /></div>
              <span className="font-medium text-sm">Añadir Conocimiento</span>
            </div>
            <ArrowRight className="w-4 h-4 text-muted-foreground group-hover:text-primary transition-colors" />
          </div>
          <div onClick={() => router.push('/dashboard/channels')} className="p-4 rounded-xl border border-border bg-card hover:bg-white/5 hover:border-white/20 transition cursor-pointer group flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-500/10 rounded-lg text-green-500"><MessageSquare className="w-5 h-5" /></div>
              <span className="font-medium text-sm">Configurar WhatsApp</span>
            </div>
            <ArrowRight className="w-4 h-4 text-muted-foreground group-hover:text-primary transition-colors" />
          </div>
        </div>
      </div>

      {/* KPIS */}
      {loading ? (
        <div className="grid gap-4 md:grid-cols-3">
          {[1, 2, 3].map(i => (
            <div key={i} className="rounded-xl border border-border bg-card p-6 h-[120px] animate-pulse flex flex-col justify-center gap-3">
              <div className="h-4 bg-muted rounded w-1/2"></div>
              <div className="h-8 bg-muted rounded w-3/4"></div>
            </div>
          ))}
        </div>
      ) : stats ? (
        <div>
          <h3 className="text-sm font-semibold text-muted-foreground mb-4 uppercase tracking-wider">Métricas Clave</h3>
          <div className="grid gap-4 md:grid-cols-3">
            <div className="rounded-xl border border-border bg-card p-6 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden group">
              <div className="absolute right-0 top-0 w-24 h-24 bg-primary/5 rounded-bl-full transition-colors group-hover:bg-primary/10"></div>
              <h3 className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                <MessageSquare className="w-4 h-4 text-primary" />
                Conversaciones Activas
              </h3>
              <div className="text-3xl font-bold mt-2 text-foreground">{stats.kpis.total_conversaciones}</div>
            </div>

            <div className="rounded-xl border border-border bg-card p-6 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden group">
              <div className="absolute right-0 top-0 w-24 h-24 bg-blue-500/5 rounded-bl-full transition-colors group-hover:bg-blue-500/10"></div>
              <h3 className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                <Users className="w-4 h-4 text-blue-500" />
                Leads Capturados
              </h3>
              <div className="text-3xl font-bold mt-2 text-foreground">{stats.kpis.leads_capturados}</div>
            </div>

            <div className="rounded-xl border border-border bg-card p-6 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden group">
              <div className="absolute right-0 top-0 w-24 h-24 bg-yellow-500/5 rounded-bl-full transition-colors group-hover:bg-yellow-500/10"></div>
              <h3 className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                <Zap className="w-4 h-4 text-yellow-500" />
                Consumo de Tokens
              </h3>
              <div className="text-3xl font-bold mt-2 text-foreground">{stats.kpis.uso_tokens.toLocaleString()}</div>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
