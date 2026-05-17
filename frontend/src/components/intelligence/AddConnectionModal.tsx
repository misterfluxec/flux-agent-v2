'use client';

import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { api } from '@/lib/api/axios';

interface Props {
  onClose: () => void;
  onAdded: () => void;
}

type ConnectionType = 'sql_server' | 'google_sheets' | 'csv_local' | null;

export function AddConnectionModal({ onClose, onAdded }: Props) {
  const [selectedType, setSelectedType] = useState<ConnectionType>(null);
  
  // Generic form state
  const [name, setName] = useState('');
  
  // SQL Server specific
  const [host, setHost] = useState('');
  const [database, setDatabase] = useState('');
  const [user, setUser] = useState('');
  const [password, setPassword] = useState('');
  const [query, setQuery] = useState('');

  // Google Sheets specific
  const [sheetId, setSheetId] = useState('');
  const [range, setRange] = useState('');
  
  // Error state
  const [error, setError] = useState<string | null>(null);

  const createConnection = useMutation({
    mutationFn: async (payload: any) => {
      return api.post('/api/v1/intelligence/connections', payload);
    },
    onSuccess: () => {
      onAdded();
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Error al crear la conexión');
    }
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    
    if (!name.trim()) {
      setError('El name de la conexión es obligatorio');
      return;
    }

    let config = {};
    if (selectedType === 'sql_server') {
      config = { host, database, user, password, query };
    } else if (selectedType === 'google_sheets') {
      config = { sheet_id: sheetId, range };
    } else if (selectedType === 'csv_local') {
      config = {}; // Simplification for now, usually would involve uploading a file
    }

    createConnection.mutate({
      name,
      type: selectedType,
      config
    });
  };

  const renderTypeSelector = () => (
    <>
      <h3 className="text-xl font-bold mb-4 text-white">Conectar Nueva Fuente</h3>
      <div className="space-y-3">
        <button 
          onClick={() => setSelectedType('sql_server')}
          className="w-full p-3 bg-slate-800 hover:bg-slate-700 text-white rounded flex items-center gap-3 transition"
        >
          <span className="text-xl">🗄️</span> SQL Server (ERP Local)
        </button>
        <button 
          onClick={() => setSelectedType('google_sheets')}
          className="w-full p-3 bg-slate-800 hover:bg-slate-700 text-white rounded flex items-center gap-3 transition"
        >
          <span className="text-xl">📊</span> Google Sheets
        </button>
        <button 
          onClick={() => setSelectedType('csv_local')}
          className="w-full p-3 bg-slate-800 hover:bg-slate-700 text-white rounded flex items-center gap-3 transition"
        >
          <span className="text-xl">📄</span> Subir Excel/CSV
        </button>
      </div>
      <button onClick={onClose} className="mt-4 text-slate-400 hover:text-white text-sm">Cancelar</button>
    </>
  );

  const renderForm = () => (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-xl font-bold text-white">
          {selectedType === 'sql_server' ? 'Conexión SQL Server' : 
           selectedType === 'google_sheets' ? 'Conexión Google Sheets' : 
           'Subir Archivo'}
        </h3>
        <button type="button" onClick={() => setSelectedType(null)} className="text-slate-400 hover:text-white text-sm">
          ← Volver
        </button>
      </div>

      <div>
        <label className="block text-sm font-medium text-slate-300 mb-1">Nombre de la Conexión</label>
        <input 
          type="text" 
          value={name} 
          onChange={e => setName(e.target.value)} 
          placeholder="Ej: ERP Ventas 2024"
          className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-cyan-500"
          required
        />
      </div>

      {selectedType === 'sql_server' && (
        <>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">Host / IP</label>
              <input 
                type="text" 
                value={host} 
                onChange={e => setHost(e.target.value)} 
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-cyan-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">Base de Datos</label>
              <input 
                type="text" 
                value={database} 
                onChange={e => setDatabase(e.target.value)} 
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-cyan-500"
                required
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">Usuario</label>
              <input 
                type="text" 
                value={user} 
                onChange={e => setUser(e.target.value)} 
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-cyan-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">Contraseña</label>
              <input 
                type="password" 
                value={password} 
                onChange={e => setPassword(e.target.value)} 
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-cyan-500"
                required
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Consulta SQL (Custom Query)</label>
            <textarea 
              value={query} 
              onChange={e => setQuery(e.target.value)} 
              placeholder="SELECT sku, name, price, stock FROM dbo.Products"
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white font-mono text-sm h-24 focus:outline-none focus:border-cyan-500"
            />
          </div>
        </>
      )}

      {selectedType === 'google_sheets' && (
        <>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">ID del Documento (Sheet ID)</label>
            <input 
              type="text" 
              value={sheetId} 
              onChange={e => setSheetId(e.target.value)} 
              placeholder="1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white font-mono focus:outline-none focus:border-cyan-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Rango (Ej: Sheet1!A1:D)</label>
            <input 
              type="text" 
              value={range} 
              onChange={e => setRange(e.target.value)} 
              placeholder="Inventario!A1:Z"
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-cyan-500"
              required
            />
          </div>
          <div className="p-3 bg-blue-900/30 border border-blue-500/30 rounded-lg text-sm text-blue-200">
            ℹ️ Asegúrate de haber compartido el documento de Sheets con la cuenta de servicio de FluxAgent.
          </div>
        </>
      )}

      {selectedType === 'csv_local' && (
        <div className="p-8 border-2 border-dashed border-slate-600 rounded-xl text-center">
          <p className="text-slate-300 mb-2">Arrastra tu archivo CSV o Excel aquí</p>
          <button type="button" className="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded text-sm text-white">Seleccionar Archivo</button>
        </div>
      )}

      {error && (
        <div className="p-3 bg-red-900/30 border border-red-500/30 rounded-lg text-sm text-red-300">
          ❌ {error}
        </div>
      )}

      <div className="flex justify-end gap-3 pt-4 border-t border-slate-700">
        <button 
          type="button" 
          onClick={onClose} 
          className="px-4 py-2 text-slate-300 hover:text-white"
        >
          Cancelar
        </button>
        <button 
          type="submit" 
          disabled={createConnection.isPending}
          className="px-6 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg font-medium transition disabled:opacity-50"
        >
          {createConnection.isPending ? 'Conectando...' : 'Probar y Guardar'}
        </button>
      </div>
    </form>
  );

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-slate-900 border border-slate-700 p-6 rounded-xl w-full max-w-lg shadow-2xl">
        {!selectedType ? renderTypeSelector() : renderForm()}
      </div>
    </div>
  );
}
