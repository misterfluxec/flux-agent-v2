'use client';

import React from 'react';
import { Columns, ArrowRight } from 'lucide-react';

export default function StepColumnMapper({ wizard }: { wizard: any }) {
  const { form } = wizard;
  const sourceType = form.watch('sourceType');

  // Si no es un archivo, este paso podría no ser tan relevante, pero lo mantenemos visualmente por el flujo.
  if (sourceType !== 'file') {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-4 text-center animate-in fade-in slide-in-from-bottom-4 duration-300">
        <div className="p-4 bg-surface-2 rounded-full text-muted-foreground">
          <Columns size={32} />
        </div>
        <div className="space-y-1">
          <h3 className="text-xl font-medium text-foreground">Sin mapeo requerido</h3>
          <p className="text-sm text-muted-foreground max-w-sm">
            Para la fuente web no es necesario mapear columnas estructuradas. El agente procesará el texto automáticamente.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col gap-6 animate-in fade-in slide-in-from-bottom-4 duration-300">
      <div className="space-y-2">
        <h3 className="text-xl font-medium text-foreground">Mapeo Inteligente</h3>
        <p className="text-sm text-muted-foreground">
          Alinea los campos de tu archivo con las propiedades que el agente IA necesita entender mejor. (Simulado)
        </p>
      </div>

      <div className="bg-surface-2 border border-border rounded-lg p-6 space-y-4">
        <div className="flex items-center justify-between text-sm font-medium text-muted-foreground mb-2">
          <span>Campos del Sistema (IA)</span>
          <span>Columnas de tu Archivo</span>
        </div>

        {/* Simulamos algunos campos */}
        {['Nombre del Producto', 'Precio', 'Descripción', 'Stock'].map((field, idx) => (
          <div key={idx} className="flex items-center gap-4">
            <div className="flex-1 bg-surface p-2 rounded-md border border-border text-sm font-medium text-foreground">
              {field}
            </div>
            <ArrowRight size={16} className="text-muted-foreground shrink-0" />
            <div className="flex-1">
              <select className="w-full bg-surface border border-border rounded-md py-2 px-3 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary">
                <option value="">Auto-detectar...</option>
                <option value="col1">Columna {idx + 1}</option>
                <option value="col2">Otra columna</option>
              </select>
            </div>
          </div>
        ))}
      </div>
      
      <p className="text-xs text-muted-foreground text-center">
        * En esta versión, la ingesta general parseará todo el texto automáticamente para RAG si no seleccionas mapeo.
      </p>
    </div>
  );
}
