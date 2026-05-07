import React from 'react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { TrendingUp, Users, DollarSign, Activity } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  trend: string;
  icon: any;
  color: string;
}

function MetricCard({ title, value, trend, icon: Icon, color }: MetricCardProps) {
  const isPositive = trend.startsWith('+');
  return (
    <div className="bg-gray-900/40 border border-gray-800/50 rounded-2xl p-6 shadow-card hover:border-gray-700/50 transition-all group overflow-hidden relative">
      <div className={`absolute top-0 right-0 w-24 h-24 bg-${color}-500/5 blur-3xl rounded-full -mr-8 -mt-8 group-hover:bg-${color}-500/10 transition-colors`} />
      <div className="flex justify-between items-start relative z-10">
        <div className="space-y-1">
          <p className="text-xs font-bold text-gray-500 uppercase tracking-widest">{title}</p>
          <p className="text-3xl font-black text-white">{value}</p>
          <div className="flex items-center gap-1.5 mt-2">
            <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${isPositive ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/10 text-rose-400'}`}>
              {trend}
            </span>
            <span className="text-[10px] text-gray-600 font-medium">vs mes anterior</span>
          </div>
        </div>
        <div className={`p-3 bg-${color}-500/10 rounded-xl border border-${color}-500/20 text-${color}-400`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
    </div>
  );
}

export function MetricsGrid({ conversations, revenue, conversion }: any) {
  // Datos de ejemplo si no vienen del prop
  const data = conversations?.history || [
    { day: 'Lun', count: 12 },
    { day: 'Mar', count: 18 },
    { day: 'Mié', count: 15 },
    { day: 'Jue', count: 25 },
    { day: 'Vie', count: 32 },
    { day: 'Sáb', count: 28 },
    { day: 'Dom', count: 20 },
  ];

  return (
    <div className="space-y-6 animate-slide-up">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <MetricCard 
          title="Conversaciones" 
          value={conversations?.total || '128'} 
          trend="+12%" 
          icon={Users} 
          color="indigo" 
        />
        <MetricCard 
          title="Tasa de Cierre" 
          value={`${conversion?.rate || '4.8'}%`} 
          trend="+5%" 
          icon={TrendingUp} 
          color="emerald" 
        />
        <MetricCard 
          title="Ingreso Estimado" 
          value={`$${revenue?.total || '2,450'}`} 
          trend="+8%" 
          icon={DollarSign} 
          color="purple" 
        />
      </div>
      
      <div className="bg-gray-900/40 border border-gray-800/50 rounded-2xl p-6 shadow-card overflow-hidden relative">
        <div className="flex items-center justify-between mb-8">
          <div className="space-y-1">
            <h4 className="text-lg font-bold text-white flex items-center gap-2">
              <Activity className="w-5 h-5 text-indigo-400" />
              Actividad Semanal
            </h4>
            <p className="text-xs text-gray-500">Volumen de interacciones de Yanua en tiempo real</p>
          </div>
          <div className="flex gap-2">
             <div className="flex items-center gap-1.5 px-3 py-1.5 bg-indigo-500/10 border border-indigo-500/20 rounded-lg">
                <div className="w-2 h-2 bg-indigo-500 rounded-full animate-pulse" />
                <span className="text-[10px] font-bold text-indigo-400 uppercase">Live</span>
             </div>
          </div>
        </div>

        <div className="h-[280px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={false} opacity={0.1} />
              <XAxis 
                dataKey="day" 
                stroke="#4b5563" 
                fontSize={11} 
                tickLine={false} 
                axisLine={false} 
                dy={10} 
              />
              <YAxis 
                stroke="#4b5563" 
                fontSize={11} 
                tickLine={false} 
                axisLine={false} 
                dx={-10}
              />
              <Tooltip 
                contentStyle={{ 
                  background: '#0f172a', 
                  border: '1px solid #1e293b', 
                  borderRadius: '12px',
                  boxShadow: '0 10px 15px -3px rgba(0,0,0,0.5)'
                }}
                itemStyle={{ color: '#818cf8', fontWeight: 'bold' }}
                cursor={{ stroke: '#4f46e5', strokeWidth: 2, strokeDasharray: '4 4' }}
              />
              <Area 
                type="monotone" 
                dataKey="count" 
                stroke="#6366f1" 
                strokeWidth={3}
                fillOpacity={1} 
                fill="url(#colorCount)" 
                animationDuration={2000}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
