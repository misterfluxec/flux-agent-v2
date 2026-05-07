'use client';

import React, { useEffect, useRef } from 'react';
import { Loader2, CheckCircle2, AlertCircle } from 'lucide-react';

export default function StepProcessing({ wizard }: { wizard: any }) {
  const { progress, logs } = wizard;
  const logsEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll logs
  useEffect(() => {
    if (logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs]);

  const isCompleted = progress.status === 'completed';
  const isError = progress.status === 'error';

  return (
    <div className="flex-1 flex flex-col gap-8 animate-in fade-in zoom-in-95 duration-300 items-center justify-center py-8">
      
      {/* Indicador principal */}
      <div className="relative flex items-center justify-center w-32 h-32">
        {/* Anillo de progreso SVG */}
        <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
          <circle
            cx="50" cy="50" r="45"
            fill="transparent"
            stroke="var(--color-surface-2)"
            strokeWidth="8"
          />
          <circle
            cx="50" cy="50" r="45"
            fill="transparent"
            stroke={isError ? "var(--color-error)" : isCompleted ? "var(--color-success)" : "var(--color-primary)"}
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray="283"
            strokeDashoffset={283 - (283 * progress.percentage) / 100}
            className="transition-all duration-500 ease-out"
          />
        </svg>

        {/* Contenido central del anillo */}
        <div className="absolute flex flex-col items-center justify-center">
          {isCompleted ? (
            <CheckCircle2 size={40} className="text-success animate-in zoom-in" />
          ) : isError ? (
            <AlertCircle size={40} className="text-error animate-in zoom-in" />
          ) : (
            <div className="flex flex-col items-center">
              <span className="text-3xl font-bold text-foreground">{progress.percentage}%</span>
            </div>
          )}
        </div>
      </div>

      <div className="text-center space-y-2">
        <h3 className="text-xl font-medium text-foreground">
          {isCompleted ? '¡Ingesta Completada!' : isError ? 'Error en Ingesta' : 'Procesando Conocimiento...'}
        </h3>
        <p className="text-sm text-muted-foreground flex items-center justify-center gap-2">
          {!isCompleted && !isError && <Loader2 size={14} className="animate-spin text-primary" />}
          {progress.currentStep}
        </p>
      </div>

      {/* Consola de logs en tiempo real */}
      <div className="w-full max-w-md bg-surface-2 border border-border rounded-lg p-4 h-48 overflow-y-auto font-mono text-xs text-muted-foreground space-y-2 shadow-inner">
        {logs.map((log: string, idx: number) => (
          <div key={idx} className="animate-in fade-in slide-in-from-bottom-1">
            <span className="text-primary/70 mr-2">{'>'}</span>
            {log}
          </div>
        ))}
        {logs.length === 0 && (
          <div className="italic opacity-50">Esperando eventos del servidor...</div>
        )}
        <div ref={logsEndRef} />
      </div>

      {isError && (
        <button 
          onClick={() => wizard.jumpToStep(4)}
          className="mt-4 px-4 py-2 bg-surface-2 text-foreground rounded-md hover:bg-surface transition-colors border border-border"
        >
          Volver e intentar de nuevo
        </button>
      )}
    </div>
  );
}
