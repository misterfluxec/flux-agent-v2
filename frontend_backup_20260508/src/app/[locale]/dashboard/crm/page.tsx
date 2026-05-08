"use client";

import { useEffect, useState, useCallback } from "react";
import { 
  Users, Plus, Search, MessageSquare, Eye, Edit, RefreshCw, Filter, Mail, Phone, Calendar, Trash2
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { fetchLeads, type LeadData } from "@/lib/api";

const statusColors: Record<string, string> = {
  nuevo: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400",
  contactado: "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400",
  interesado: "bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400",
  cerrado: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400",
  perdido: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
};

const sourceLabels: Record<string, string> = {
  whatsapp: "WhatsApp",
  telegram: "Telegram",
  web: "Web",
  email: "Email",
};

export default function CRMPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const [filterEstado, setFilterEstado] = useState("all");
  const [filterOrigen, setFilterOrigen] = useState("all");
  const [leadsData, setLeadsData] = useState<LeadData[]>([]);
  const [loading, setLoading] = useState(true);

  const loadLeads = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchLeads();
      setLeadsData(data);
    } catch (err) {
      console.error("Error fetching leads:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadLeads();
  }, [loadLeads]);

  const stats = {
    total: leadsData.length,
    nuevos: leadsData.filter(l => l.estado === "nuevo").length,
    contactados: leadsData.filter(l => l.estado === "contactado").length,
    interesados: leadsData.filter(l => l.estado === "interesado").length,
    cerrados: leadsData.filter(l => l.estado === "cerrado").length,
    perdido: leadsData.filter(l => l.estado === "perdido").length,
  };

  const filteredLeads = leadsData.filter(lead => {
    const matchesSearch = lead.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
                          lead.phone.includes(searchTerm) ||
                          lead.email.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilterEstado = filterEstado === "all" || lead.estado === filterEstado;
    const matchesFilterOrigen = filterOrigen === "all" || lead.canal === filterOrigen;
    return matchesSearch && matchesFilterEstado && matchesFilterOrigen;
  });

  return (
    <div className="space-y-6 max-w-7xl mx-auto animate-entry">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <Users className="w-6 h-6 text-indigo-500" />
            Clientes & Leads
          </h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1 text-sm">
            Gestiona tu base de clientes y oportunidades de venta
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={loadLeads}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-slate-700 dark:text-slate-200 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800/50 transition shadow-sm disabled:opacity-50"
          >
            <RefreshCw size={16} className={loading ? "animate-spin" : ""} />
            Actualizar
          </button>
          <button className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 transition shadow-sm">
            <Plus className="w-4 h-4" />
            Nuevo Cliente
          </button>
        </div>
      </div>

      {/* Stats Cards - Template Style */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        {[
          { label: "Nuevos", count: stats.nuevos },
          { label: "Contactados", count: stats.contactados },
          { label: "Interesados", count: stats.interesados },
          { label: "Cerrados", count: stats.cerrados },
          { label: "Perdidos", count: stats.perdido },
        ].map((stat) => (
          <Card key={stat.label} className="border-slate-200 dark:border-slate-800 bg-white/70 dark:bg-slate-900/70 shadow-sm">
            <CardContent className="p-4">
              <p className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">{stat.label}</p>
              <p className="text-2xl font-bold text-slate-900 dark:text-white mt-1">{stat.count}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Filters - Template Style */}
      <Card className="border-slate-200 dark:border-slate-800 bg-white/70 dark:bg-slate-900/70 shadow-sm">
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input
                placeholder="Buscar clientes..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full h-10 pl-9 pr-4 bg-transparent border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-indigo-500 placeholder:text-slate-400"
              />
            </div>
            <div className="flex gap-2">
              <div className="relative">
                <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <select 
                  value={filterEstado}
                  onChange={(e) => setFilterEstado(e.target.value)}
                  className="h-10 pl-9 pr-8 bg-transparent border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-700 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500 appearance-none"
                >
                  <option value="all" className="dark:bg-slate-900">Estado (Todos)</option>
                  <option value="nuevo" className="dark:bg-slate-900">Nuevo</option>
                  <option value="contactado" className="dark:bg-slate-900">Contactado</option>
                  <option value="interesado" className="dark:bg-slate-900">Interesado</option>
                  <option value="cerrado" className="dark:bg-slate-900">Cerrado</option>
                  <option value="perdido" className="dark:bg-slate-900">Perdido</option>
                </select>
              </div>
              <select 
                value={filterOrigen}
                onChange={(e) => setFilterOrigen(e.target.value)}
                className="h-10 px-4 bg-transparent border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-700 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              >
                <option value="all" className="dark:bg-slate-900">Origen (Todos)</option>
                <option value="whatsapp" className="dark:bg-slate-900">WhatsApp</option>
                <option value="telegram" className="dark:bg-slate-900">Telegram</option>
                <option value="web" className="dark:bg-slate-900">Web</option>
                <option value="email" className="dark:bg-slate-900">Email</option>
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Clients Table - Template Style */}
      <Card className="border-slate-200 dark:border-slate-800 bg-white/70 dark:bg-slate-900/70 shadow-sm">
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-800">
                  <th className="px-6 py-3 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Cliente</th>
                  <th className="px-6 py-3 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Contacto</th>
                  <th className="px-6 py-3 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Estado</th>
                  <th className="px-6 py-3 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Origen</th>
                  <th className="px-6 py-3 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Último Contacto</th>
                  <th className="px-6 py-3 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Monto</th>
                  <th className="px-6 py-3 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider text-right">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800/50">
                {loading && filteredLeads.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-6 py-12 text-center text-slate-400 text-sm animate-pulse">
                      Cargando clientes...
                    </td>
                  </tr>
                ) : filteredLeads.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-6 py-12 text-center text-slate-400 text-sm">
                      No se encontraron clientes con esos filtros.
                    </td>
                  </tr>
                ) : (
                  filteredLeads.map((client) => (
                    <tr key={client.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className="w-9 h-9 rounded-full bg-gradient-to-br from-slate-200 to-slate-300 dark:from-slate-700 dark:to-slate-600 flex items-center justify-center text-sm font-bold text-slate-600 dark:text-slate-300 shrink-0">
                            {client.name[0].toUpperCase()}
                          </div>
                          <div>
                            <p className="text-sm font-medium text-slate-900 dark:text-white">
                              {client.name}
                            </p>
                            <div className="flex gap-1 mt-0.5">
                              <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-500 border border-slate-200 dark:border-slate-700">
                                lead
                              </span>
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="space-y-1">
                          <div className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400">
                            <Mail className="w-3 h-3" />
                            {client.email}
                          </div>
                          <div className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400">
                            <Phone className="w-3 h-3" />
                            {client.phone}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`px-2.5 py-1 text-xs font-semibold rounded-full ${statusColors[client.estado] || statusColors.nuevo}`}>
                          {client.estado.charAt(0).toUpperCase() + client.estado.slice(1)}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
                          {sourceLabels[client.canal] || client.canal.charAt(0).toUpperCase() + client.canal.slice(1)}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400">
                          <Calendar className="w-3 h-3" />
                          {client.fecha}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className="text-sm font-medium text-slate-900 dark:text-white">
                          ${client.monto > 0 ? client.monto : "-"}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex items-center justify-end gap-1">
                          <button className="p-2 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 dark:hover:bg-indigo-500/10 rounded-md transition-colors" title="Editar">
                            <Edit className="w-4 h-4" />
                          </button>
                          <button className="p-2 text-slate-400 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-500/10 rounded-md transition-colors" title="Ver Historial">
                            <MessageSquare className="w-4 h-4" />
                          </button>
                          <button className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-500/10 rounded-md transition-colors" title="Eliminar">
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
          {filteredLeads.length > 0 && (
            <div className="px-6 py-3 border-t border-slate-200 dark:border-slate-800 text-xs text-slate-500 dark:text-slate-400 bg-slate-50/50 dark:bg-slate-900/50 rounded-b-xl flex justify-between items-center">
              <span>Mostrando {filteredLeads.length} de {leadsData.length} clientes</span>
              <div className="flex items-center gap-2">
                <button className="px-3 py-1 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded hover:bg-slate-50 dark:hover:bg-slate-700 transition">Anterior</button>
                <button className="px-3 py-1 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded hover:bg-slate-50 dark:hover:bg-slate-700 transition">Siguiente</button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
