"use client";

import { Ticket, Search, Filter, MoreVertical, Plus, Clock, CheckCircle2, AlertCircle } from "lucide-react";
import { useState } from "react";

export default function TicketsPage() {
  const [tickets] = useState([
    { id: "T-1024", subject: "Error en ingesta de PDF", priority: "Alta", status: "Abierto", user: "InnovaCorp", date: "Hace 2h" },
    { id: "T-1025", subject: "Consulta sobre API Billing", priority: "Media", status: "En Progreso", user: "EduTech", date: "Hace 4h" },
    { id: "T-1026", subject: "Aumento de cuota mensual", priority: "Baja", status: "Cerrado", user: "GlobalLogistics", date: "Ayer" },
  ]);

  const getPriorityColor = (p: string) => {
    switch(p) {
        case "Alta": return "text-red-400 bg-red-400/10 border-red-400/20";
        case "Media": return "text-amber-400 bg-amber-400/10 border-amber-400/20";
        default: return "text-blue-400 bg-blue-400/10 border-blue-400/20";
    }
  }

  return (
    <div className="space-y-8 animate-entry">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            <Ticket className="w-6 h-6 text-amber-400" />
            Gestión de Tickets
          </h1>
          <p className="text-slate-400 text-sm mt-1">Soporte técnico y atención al cliente centralizada</p>
        </div>
        <button className="bg-amber-600 hover:bg-amber-500 text-white px-4 py-2.5 rounded-xl text-sm font-bold transition-all flex items-center gap-2 shadow-lg shadow-amber-600/20">
            <Plus className="w-4 h-4" />
            Nuevo Ticket
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <KPICard label="Tickets Abiertos" val="12" icon={AlertCircle} color="text-red-400" />
          <KPICard label="En Resolución" val="5" icon={Clock} color="text-amber-400" />
          <KPICard label="Resueltos Hoy" val="28" icon={CheckCircle2} color="text-emerald-400" />
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl">
        <div className="p-4 bg-slate-950/50 border-b border-slate-800 flex justify-between items-center">
            <div className="flex gap-4">
                <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-600" />
                    <input type="text" placeholder="Buscar ticket..." className="bg-slate-900 border border-slate-800 rounded-lg py-1.5 pl-9 pr-4 text-xs text-slate-300 focus:outline-none" />
                </div>
                <button className="px-3 py-1.5 border border-slate-800 rounded-lg text-xs text-slate-400 flex items-center gap-2 hover:bg-slate-800">
                    <Filter className="w-3.5 h-3.5" />
                    Filtros
                </button>
            </div>
        </div>
        <table className="w-full text-left border-collapse">
            <thead className="bg-slate-950/30 text-[10px] uppercase tracking-widest text-slate-500 font-bold">
                <tr>
                    <th className="px-6 py-4">ID / Asunto</th>
                    <th className="px-6 py-4">Usuario / Empresa</th>
                    <th className="px-6 py-4">Prioridad</th>
                    <th className="px-6 py-4">Estado</th>
                    <th className="px-6 py-4">Última Actividad</th>
                    <th className="px-6 py-4 text-right"></th>
                </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
                {tickets.map((t) => (
                    <tr key={t.id} className="hover:bg-slate-800/30 transition-colors group">
                        <td className="px-6 py-5">
                            <div className="font-bold text-slate-200 text-sm">{t.subject}</div>
                            <div className="text-[10px] text-slate-500 font-mono mt-0.5">{t.id}</div>
                        </td>
                        <td className="px-6 py-5">
                            <div className="text-xs font-medium text-slate-300">{t.user}</div>
                        </td>
                        <td className="px-6 py-5">
                            <span className={`text-[10px] font-bold px-2 py-0.5 rounded border uppercase ${getPriorityColor(t.priority)}`}>
                                {t.priority}
                            </span>
                        </td>
                        <td className="px-6 py-5">
                            <div className="flex items-center gap-2">
                                <div className={`w-1.5 h-1.5 rounded-full ${t.status === 'Abierto' ? 'bg-red-500' : t.status === 'Cerrado' ? 'bg-emerald-500' : 'bg-amber-500'}`} />
                                <span className="text-xs text-slate-300">{t.status}</span>
                            </div>
                        </td>
                        <td className="px-6 py-5 text-xs text-slate-500">{t.date}</td>
                        <td className="px-6 py-5 text-right">
                            <button className="p-2 hover:bg-slate-700 rounded-lg text-slate-500 transition-colors">
                                <MoreVertical className="w-4 h-4" />
                            </button>
                        </td>
                    </tr>
                ))}
            </tbody>
        </table>
      </div>
    </div>
  );
}

function KPICard({ label, val, icon: Icon, color }: any) {
    return (
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl flex items-center gap-4">
            <div className={`p-3 rounded-xl bg-slate-950 border border-slate-800 ${color}`}>
                <Icon className="w-5 h-5" />
            </div>
            <div>
                <div className="text-xl font-bold text-white">{val}</div>
                <div className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">{label}</div>
            </div>
        </div>
    )
}
