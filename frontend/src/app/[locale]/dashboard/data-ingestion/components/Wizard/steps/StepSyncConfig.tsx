'use client';

import React from 'react';
import { RefreshCw, Clock } from 'lucide-react';

export default function StepSyncConfig({ wizard }: { wizard: any }) {
  const { form } = wizard;
  
  const syncEnabled = form.watch('syncEnabled');

  return (
    <div className="flex-1 flex flex-col gap-6 animate-in fade-in slide-in-from-bottom-4 duration-300">
      <div className="space-y-2">
        <h3 className="text-xl font-medium text-foreground">Sincronización Automática</h3>
        <p className="text-sm text-muted-foreground">
          Configura cada cuánto tiempo el agente debe volver a leer la fuente para mantener su conocimiento actualizado.
        </p>
      </div>

      <div className="bg-surface border border-border rounded-xl p-6 space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg ${syncEnabled ? 'bg-primary/10 text-primary' : 'bg-surface-2 text-muted-foreground'}`}>
              <RefreshCw size={24} className={syncEnabled ? 'animate-spin-slow' : ''} />
            </div>
            <div>
              <h4 className="font-medium text-foreground">Activar Sincronización</h4>
              <p className="text-sm text-muted-foreground">Mantener actualizado en segundo plano</p>
            </div>
          </div>
          
          <label className="relative inline-flex items-center cursor-pointer">
            <input 
              type="checkbox" 
              className="sr-only peer"
              {...form.register('syncEnabled')}
            />
            <div className="w-11 h-6 bg-surface-2 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
          </label>
        </div>

        {syncEnabled && (
          <div className="pt-4 border-t border-border animate-in fade-in slide-in-from-top-2 duration-200">
            <label className="text-sm font-medium text-foreground flex items-center gap-2 mb-3">
              <Clock size={16} /> Frecuencia de Sincronización
            </label>
            <select 
              {...form.register('syncFrequency')}
              className="w-full bg-surface-2 border border-border rounded-md py-2.5 px-3 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="hourly">Cada Hora</option>
              <option value="daily">Diariamente</option>
              <option value="weekly">Semanalmente</option>
              <option value="monthly">Mensualmente</option>
            </select>
            <p className="text-xs text-muted-foreground mt-2">
              Se recomienda "Diariamente" para catálogos con rotación normal de stock o precios.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
