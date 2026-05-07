'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { MessageSquare, Users, Target, Clock, TrendingUp, TrendingDown, Minus, Bot, Zap } from 'lucide-react';

import { fetchAnalyticsOverview } from '@/lib/api/analytics';
import { queryClient } from '@/lib/query-client';
import { KPICardSkeleton, ConversationsKPI, LeadsKPI, ConversionRateKPI, SentimentKPI, ResponseTimeKPI } from '@/components/ui/kpi-card';

interface StatsOverview {
  kpis: {
    total_conversaciones: number;
    leads_capturados: number;
    sentimiento_promedio: number;
    uso_tokens: number;
  };
  mensajes_por_dia: { fecha: string; conteo: number }[];
  sentimiento_distribucion: { name: string; value: number; fill: string }[];
  actividad_reciente: {
    id: string;
    action: string;
    agent: string;
    time: string;
    status: string;
  }[];
}

interface AnalyticsOverview {
  total_conversations: number;
  total_messages: number;
  total_sales: number;
  conversion_rate: number;
  avg_response_time: number;
  sentiment_score: number;
  cache_status?: 'HIT' | 'MISS';
  cache_ttl?: number;
}

export default function DashboardPage() {
  const router = useRouter();
  const [onboardingChecked, setOnboardingChecked] = useState(false);
  const [stats, setStats] = useState<StatsOverview | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchStats() {
      try {
        // Obtenemos token del localStorage que es donde login/page.tsx lo guarda
        const token = localStorage.getItem('flux_token');

        if (!token) {
          router.push('/login');
          return;
        }

        // Verificar si el usuario tiene agentes creados (más confiable que localStorage)
        const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:9000";
        
        console.log('Dashboard: Checking agents for onboarding...');
        
        const agentsRes = await fetch(`${BACKEND_URL}/api/v1/agents`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        console.log('Dashboard: Agents response status:', agentsRes.status);

        if (agentsRes.ok) {
          const agentsData = await agentsRes.json();
          const hasAgents = agentsData && agentsData.length > 0;
          
          console.log('Dashboard: Has agents:', hasAgents, 'Agents count:', agentsData?.length);
          
          if (!hasAgents) {
            // Redirigir al wizard de onboarding si no tiene agentes
            console.log('Dashboard: Redirecting to onboarding...');
            router.push('/onboarding');
            return;
          }
          
          // Si tiene agentes, marcar onboarding como completado
          if (typeof window !== 'undefined') {
            localStorage.setItem('onboarding_complete', 'true');
            document.cookie = "onboarding_complete=true; path=/; max-age=31536000";
          }
        } else {
          console.error('Dashboard: Failed to fetch agents:', agentsRes.status);
        }

        const res = await fetch(`${BACKEND_URL}/api/v1/stats/overview`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (res.ok) {
          const data = await res.json();
          setStats(data);
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
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <div className="flex gap-2">
          <button 
            onClick={() => router.push('/dashboard/agent')}
            className="bg-primary text-primary-foreground px-4 py-2 rounded-md text-sm font-medium hover:bg-primary/90 transition-colors flex items-center gap-2"
          >
            <Bot className="w-4 h-4" />
            Nuevo Agente
          </button>
        </div>
      </div>

      {loading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="rounded-xl border border-border bg-card p-6 shadow-sm h-[120px] animate-pulse flex flex-col justify-center gap-3">
              <div className="h-4 bg-muted rounded w-1/2"></div>
              <div className="h-8 bg-muted rounded w-3/4"></div>
            </div>
          ))}
        </div>
      ) : stats ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {/* KPI 1: Conversaciones */}
          <div className="rounded-xl border border-border bg-card p-6 shadow-sm hover:shadow-md transition-shadow group relative overflow-hidden">
            <div className="absolute right-4 top-4 text-primary/10 group-hover:text-primary/20 transition-colors">
              <MessageSquare className="w-12 h-12" />
            </div>
            <h3 className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <MessageSquare className="w-4 h-4 text-primary" />
              Conversaciones
            </h3>
            <div className="text-3xl font-bold mt-2">{stats.kpis.total_conversaciones}</div>
            <p className="text-xs text-green-500 mt-1 flex items-center gap-1 font-medium">
              <TrendingUp className="w-3 h-3" />
              Actividad Estable
            </p>
          </div>

          {/* KPI 2: Leads */}
          <div className="rounded-xl border border-border bg-card p-6 shadow-sm hover:shadow-md transition-shadow group relative overflow-hidden">
            <div className="absolute right-4 top-4 text-primary/10 group-hover:text-primary/20 transition-colors">
              <Users className="w-12 h-12" />
            </div>
            <h3 className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Users className="w-4 h-4 text-blue-500" />
              Leads Capturados
            </h3>
            <div className="text-3xl font-bold mt-2">{stats.kpis.leads_capturados}</div>
            <p className="text-xs text-blue-500 mt-1 flex items-center gap-1 font-medium">
              <Minus className="w-3 h-3" />
              Prospectos Únicos
            </p>
          </div>

          {/* KPI 3: Tokens */}
          <div className="rounded-xl border border-border bg-card p-6 shadow-sm hover:shadow-md transition-shadow group relative overflow-hidden">
            <div className="absolute right-4 top-4 text-primary/10 group-hover:text-primary/20 transition-colors">
              <Zap className="w-12 h-12" />
            </div>
            <h3 className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Zap className="w-4 h-4 text-yellow-500" />
              Uso de Tokens
            </h3>
            <div className="text-3xl font-bold mt-2">{stats.kpis.uso_tokens.toLocaleString()}</div>
            <p className="text-xs text-yellow-600 mt-1 flex items-center gap-1 font-medium">
              Llamadas a Ollama
            </p>
          </div>

          {/* KPI 4: Sentimiento */}
          <div className="rounded-xl border border-border bg-card p-6 shadow-sm hover:shadow-md transition-shadow group relative overflow-hidden">
            <h3 className="text-sm font-medium text-muted-foreground">Sentimiento Promedio</h3>
            <div className="text-3xl font-bold mt-2">
              {stats.kpis.sentimiento_promedio > 0.3 ? '😊' : stats.kpis.sentimiento_promedio < -0.3 ? '😡' : '😐'}
            </div>
            <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1 font-medium">
              {(stats.kpis.sentimiento_promedio * 100).toFixed(0)}% Score
            </p>
          </div>
        </div>
      ) : null}

      {/* Actividad Reciente */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 rounded-xl border border-border bg-card p-6 shadow-sm">
          <h2 className="text-lg font-semibold mb-4">Métricas de Conectores (Fase 4)</h2>
          <div className="h-[300px] flex flex-col items-center justify-center text-muted-foreground bg-muted/30 rounded-lg border border-dashed border-border">
            <Bot className="w-8 h-8 mb-2 opacity-50" />
            <p className="font-medium">Web Widget & Shopify</p>
            <p className="text-sm">Configura tus canales en la pestaña superior para ver métricas de ROI.</p>
          </div>
        </div>

        <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
          <h2 className="text-lg font-semibold mb-4">Actividad Reciente</h2>
          {stats?.actividad_reciente && stats.actividad_reciente.length > 0 ? (
            <div className="space-y-4">
              {stats.actividad_reciente.map((act) => (
                <div key={act.id} className="flex items-start gap-3 border-b border-border/50 pb-3 last:border-0">
                  <div className={`w-2 h-2 rounded-full mt-2 ${act.status === 'success' ? 'bg-green-500' : 'bg-blue-500'}`} />
                  <div>
                    <p className="text-sm font-medium">{act.action}</p>
                    <p className="text-xs text-muted-foreground">Atendido por {act.agent}</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              <p className="text-sm">No hay actividad reciente</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
