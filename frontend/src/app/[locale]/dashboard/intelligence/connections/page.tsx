'use client';

import { useQuery, useMutation } from '@tanstack/react-query';
import { api } from '@/lib/api/axios';
import { PermissionGate } from '@/components/system/PermissionGate';
import { useState } from 'react';
import { AddConnectionModal } from '@/components/intelligence/AddConnectionModal';

// Iconos y Configuración Visual
const TYPE_CONFIG = {
  sql_server: { icon: '🗄️', label: 'SQL Server', color: 'bg-blue-600' },
  google_sheets: { icon: '📊', label: 'Google Sheets', color: 'bg-green-600' },
  csv_local: { icon: '📄', label: 'Archivo Local', color: 'bg-slate-600' },
  woocommerce: { icon: '🛒', label: 'WooCommerce', color: 'bg-purple-600' },
  shopify: { icon: '🛍️', label: 'Shopify', color: 'bg-cyan-600' },
};

export default function IntelligencePage() {
  const [isAdding, setIsAdding] = useState(false);

  // Cargar conexiones (Refresca automáticamente cada 15s para ver status en vivo)
  const { data: connections, isLoading, refetch } = useQuery({
    queryKey: ['connections'],
    queryFn: () => api.get('/api/v1/intelligence/connections').then(res => res.data),
    refetchInterval: 15000, 
  });

  // Mutación para disparar Sync manual
  const triggerSync = useMutation({
    mutationFn: (id: string) => api.post(`/api/v1/intelligence/connections/${id}/sync`),
    onSuccess: () => refetch(), // Refrescar lista tras sync
  });

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-white">🧠 Inteligencia de Datos</h1>
          <p className="text-slate-400">Monitorea la salud de tus conexiones y sincroniza inventario en tiempo real.</p>
        </div>
        <PermissionGate feature="manage_connections">
          <button 
            onClick={() => setIsAdding(true)}
            className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 rounded-lg text-white font-medium transition"
          >
            + Nueva Conexión
          </button>
        </PermissionGate>
      </div>

      {/* Grid de Conexiones */}
      {isLoading ? (
        <div className="text-center py-20 text-slate-500">Cargando status de conexiones...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {connections?.map((conn: any) => (
            <ConnectionCard key={conn.id} conn={conn} onSync={() => triggerSync.mutate(conn.id)} />
          ))}
        </div>
      )}

      {connections?.length === 0 && !isLoading && (
        <div className="text-center py-20 border-2 border-dashed border-slate-700 rounded-xl">
          <p className="text-xl text-slate-400">📭 Sin conexiones activas</p>
          <p className="text-slate-500 mt-2">Conecta tu primer archivo o base de datos para comenzar.</p>
        </div>
      )}

      {isAdding && (
        <AddConnectionModal 
          onClose={() => setIsAdding(false)} 
          onAdded={() => { setIsAdding(false); refetch(); }} 
        />
      )}
    </div>
  );
}

// Componente Tarjeta de Conexión Individual
function ConnectionCard({ conn, onSync }: { conn: any, onSync: () => void }) {
  const config = TYPE_CONFIG[conn.connection_type as keyof typeof TYPE_CONFIG] || TYPE_CONFIG.csv_local;

  // Determinar color del status
  const statusColors: any = {
    active: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    error: 'bg-red-500/10 text-red-400 border-red-500/20',
    syncing: 'bg-blue-500/10 text-blue-400 border-blue-500/20 animate-pulse',
    inactive: 'bg-slate-500/10 text-slate-400 border-slate-500/20'
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 hover:border-slate-600 transition relative overflow-hidden">
      {/* Barra lateral de color según type */}
      <div className={`absolute left-0 top-0 bottom-0 w-1 ${config.color}`}></div>

      <div className="flex justify-between items-start mb-4">
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 rounded-lg ${config.color} flex items-center justify-center text-lg`}>
            {config.icon}
          </div>
          <div>
            <h3 className="font-bold text-white">{conn.name}</h3>
            <p className="text-xs text-slate-400">{config.label}</p>
          </div>
        </div>
        <span className={`text-[10px] font-bold px-2 py-1 rounded-full border uppercase ${statusColors[conn.status] || statusColors.inactive}`}>
          {conn.status === 'syncing' ? '🔄 Sync...' : conn.status}
        </span>
      </div>

      {/* Métricas Clave */}
      <div className="grid grid-cols-2 gap-y-3 gap-x-4 text-sm mb-5">
        <div>
          <p className="text-slate-500 text-xs">Última Actualización</p>
          <p className="text-slate-200 font-mono text-xs">
            {conn.last_sync_at ? new Date(conn.last_sync_at).toLocaleTimeString() : 'Nunca'}
          </p>
        </div>
        <div>
          <p className="text-slate-500 text-xs">Próxima Sync</p>
          <p className="text-slate-200 font-mono text-xs">
            {conn.next_sync_at ? 'Automática' : 'Manual'}
          </p>
        </div>
        <div>
          <p className="text-slate-500 text-xs">Productos Cargados</p>
          <p className="text-emerald-400 font-bold">{conn.total_rows_synced || 0}</p>
        </div>
        <div>
          <p className="text-slate-500 text-xs">Frecuencia</p>
          <p className="text-slate-200 text-xs">{conn.sync_frequency || '1h'}</p>
        </div>
      </div>

      {/* Mensaje de Error si existe */}
      {conn.last_error_message && (
        <div className="mb-4 p-2 bg-red-900/20 border border-red-500/30 rounded text-xs text-red-300">
          ⚠️ {conn.last_error_message}
        </div>
      )}

      {/* Acciones */}
      <div className="flex gap-2">
        <button 
          onClick={onSync}
          disabled={conn.status === 'syncing'}
          className="flex-1 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded transition disabled:opacity-50"
        >
          🔄 Sincronizar Ahora
        </button>
        <button className="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-400 rounded transition">
          ⚙️
        </button>
      </div>
    </div>
  );
}
