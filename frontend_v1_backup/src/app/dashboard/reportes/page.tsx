"use client";

import { PieChart, TrendingUp, BarChart3, Users } from "lucide-react";

export default function ReportesPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-100">Reportes & Analytics</h1>
        <p className="text-sm text-slate-400 mt-1">
          Métricas de rendimiento de tu negocio y agente IA.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* KPI Cards Stub */}
        {[
          { label: "Total Conversaciones", value: "0", icon: Users, color: "text-blue-500", bg: "bg-blue-500/10" },
          { label: "Tasa de Respuesta", value: "0%", icon: TrendingUp, color: "text-emerald-500", bg: "bg-emerald-500/10" },
          { label: "Atención IA", value: "0%", icon: PieChart, color: "text-indigo-500", bg: "bg-indigo-500/10" },
          { label: "Leads Generados", value: "0", icon: BarChart3, color: "text-amber-500", bg: "bg-amber-500/10" },
        ].map((kpi, i) => (
          <div key={i} className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex items-center gap-4">
            <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${kpi.bg}`}>
              <kpi.icon className={kpi.color} size={24} strokeWidth={2} />
            </div>
            <div>
              <p className="text-xs font-medium text-slate-400">{kpi.label}</p>
              <h3 className="text-2xl font-bold text-slate-100">{kpi.value}</h3>
            </div>
          </div>
        ))}
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 text-center flex flex-col items-center justify-center min-h-[400px]">
        <div className="w-16 h-16 bg-slate-800 rounded-full flex items-center justify-center mb-4">
          <PieChart size={32} className="text-slate-400" />
        </div>
        <h3 className="text-lg font-bold text-slate-200">Gráficos en Construcción</h3>
        <p className="text-sm text-slate-400 mt-2 max-w-md">
          Próximamente podrás visualizar el funnel de conversión, volumen de mensajes diarios y rendimiento por canal.
        </p>
      </div>
    </div>
  );
}
