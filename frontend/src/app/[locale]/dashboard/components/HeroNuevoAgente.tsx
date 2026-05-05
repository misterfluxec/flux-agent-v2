'use client';

import React from 'react';
import { Bot, Sparkles, Rocket, ChevronRight, CheckCircle2 } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface HeroNuevoAgenteProps {
  onStart: () => void;
}

export default function HeroNuevoAgente({ onStart }: HeroNuevoAgenteProps) {
  const steps = [
    { id: 1, label: 'Identidad', icon: Bot },
    { id: 2, label: 'Guión', icon: Sparkles },
    { id: 3, label: 'Datos', icon: Rocket },
    { id: 4, label: 'Canal', icon: ChevronRight },
    { id: 5, label: 'Validar', icon: CheckCircle2 },
  ];

  return (
    <div className="relative min-h-[80vh] flex flex-col items-center justify-center overflow-hidden rounded-3xl bg-slate-950 p-6 text-center border border-slate-800">
      {/* Background decoration */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-indigo-500/10 via-transparent to-transparent -z-10" />
      <div className="absolute -top-24 -left-24 w-96 h-96 bg-indigo-600/5 rounded-full blur-3xl -z-10" />
      <div className="absolute -bottom-24 -right-24 w-96 h-96 bg-purple-600/5 rounded-full blur-3xl -z-10" />

      {/* Main Content */}
      <div className="relative z-10 max-w-2xl w-full space-y-8 animate-in fade-in zoom-in duration-700">
        <div className="flex justify-center">
          <div className="relative">
            <div className="w-24 h-24 rounded-full bg-gradient-to-tr from-indigo-600 to-purple-600 flex items-center justify-center shadow-[0_0_40px_rgba(79,70,229,0.4)] animate-pulse">
              <Bot size={48} className="text-white" />
            </div>
            <div className="absolute -inset-4 border-2 border-dashed border-indigo-500/30 rounded-full animate-spin-slow" />
          </div>
        </div>

        <div className="space-y-4">
          <h1 className="text-4xl md:text-5xl font-extrabold text-white tracking-tight leading-tight">
            Tu Agente de Ventas está listo para adquirir sus <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400">SUPER PODERES</span> 🚀
          </h1>
          <p className="text-lg text-slate-400 max-w-lg mx-auto">
            Con VentaCore AI, tu agente aprenderá tu negocio, atenderá clientes 24/7 y cerrará ventas mientras duermes.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
          <Button 
            onClick={onStart}
            size="lg"
            className="h-14 px-8 rounded-2xl bg-indigo-600 hover:bg-indigo-700 text-white text-lg font-bold shadow-[0_0_20px_rgba(79,70,229,0.3)] hover:shadow-[0_0_30px_rgba(79,70,229,0.5)] transition-all group"
          >
            <Sparkles className="mr-2 group-hover:rotate-12 transition-transform" />
            Iniciar Entrenamiento
          </Button>
          <Button 
            variant="outline" 
            size="lg"
            className="h-14 px-8 rounded-2xl border-slate-700 bg-slate-900/50 text-slate-300 hover:bg-slate-800"
          >
            Ver Demo
          </Button>
        </div>

        {/* Unlocking Roadmap */}
        <div className="pt-12 space-y-6">
          <p className="text-xs font-bold uppercase tracking-[0.2em] text-slate-500">Lo que desbloquearás</p>
          <div className="flex items-center justify-between max-w-md mx-auto relative">
            <div className="absolute top-1/2 left-0 right-0 h-0.5 bg-slate-800 -z-10" />
            {steps.map((step) => {
              const Icon = step.icon;
              return (
                <div key={step.id} className="flex flex-col items-center gap-2 group">
                  <div className="w-10 h-10 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-center text-slate-500 group-hover:border-indigo-500/50 transition-colors">
                    <Icon size={18} />
                  </div>
                  <span className="text-[10px] font-medium text-slate-300">{step.label}</span>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      <style jsx>{`
        .animate-spin-slow {
          animation: spin 8s linear infinite;
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
