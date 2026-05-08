"use client";

import { useState, useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import {
  Bot, Plug, Brain, MessageSquare, CheckCircle2,
  ChevronRight, Sparkles, Loader2, Rocket, X,
} from "lucide-react";
import { fetchAgents, fetchKnowledge } from "@/lib/api";

// =============================================================================
// ONBOARDING WIZARD — Primera Victoria en <15 min
// Se muestra en el Dashboard Home si el tenant no ha completado el setup.
// Se auto-oculta al completar todos los pasos.
// =============================================================================

interface Step {
  id: string;
  label: string;
  desc: string;
  icon: any;
  href: string;
  check: () => Promise<boolean>;
}

const STEPS: Step[] = [
  {
    id: "agent",
    label: "Crear tu primer Agente IA",
    desc: "Dale nombre, personalidad y un propósito a tu workforce digital",
    icon: Bot,
    href: "/dashboard/agents",
    check: async () => {
      try {
        const agents = await fetchAgents();
        return agents.length > 0;
      } catch { return false; }
    },
  },
  {
    id: "channel",
    label: "Conectar un Canal",
    desc: "WhatsApp, Web Chat o Telegram — elige al menos uno",
    icon: Plug,
    href: "/dashboard/connectors",
    check: async () => {
      try {
        // Check if any agent has channels configured
        const agents = await fetchAgents();
        return agents.some(a => a.canales && a.canales.length > 0);
      } catch { return false; }
    },
  },
  {
    id: "knowledge",
    label: "Cargar Conocimiento",
    desc: "Sube PDFs, URLs o productos para que tu IA aprenda tu negocio",
    icon: Brain,
    href: "/dashboard/data-ingestion",
    check: async () => {
      try {
        const k = await fetchKnowledge();
        return (k.total_chunks || 0) > 0;
      } catch { return false; }
    },
  },
  {
    id: "conversation",
    label: "Recibir tu Primer Lead",
    desc: "Prueba tu agente desde el chat web o envía un mensaje de WhatsApp",
    icon: MessageSquare,
    href: "/dashboard/conversations",
    check: async () => {
      // For now, check localStorage flag or agents with test activity
      return localStorage.getItem("flux_first_lead") === "true";
    },
  },
];

export function OnboardingWizard() {
  const [stepStatus, setStepStatus] = useState<Record<string, boolean>>({});
  const [loading, setLoading] = useState(true);
  const [dismissed, setDismissed] = useState(false);
  const router = useRouter();
  const pathname = usePathname();
  const segments = pathname.split("/");
  const locale = segments[1] || "es";

  useEffect(() => {
    if (localStorage.getItem("flux_onboarding_dismissed") === "true") {
      setDismissed(true);
      return;
    }

    (async () => {
      setLoading(true);
      const results: Record<string, boolean> = {};
      for (const step of STEPS) {
        results[step.id] = await step.check();
      }
      setStepStatus(results);
      setLoading(false);
    })();
  }, []);

  const completedCount = Object.values(stepStatus).filter(Boolean).length;
  const allDone = completedCount === STEPS.length;

  // Auto-dismiss when all complete
  useEffect(() => {
    if (allDone && !loading) {
      localStorage.setItem("flux_onboarding_dismissed", "true");
    }
  }, [allDone, loading]);

  if (dismissed || allDone || loading) return null;

  const handleDismiss = () => {
    setDismissed(true);
    localStorage.setItem("flux_onboarding_dismissed", "true");
  };

  return (
    <div className="bg-gradient-to-r from-cyan-500/5 via-transparent to-transparent border border-cyan-500/10 rounded-2xl p-5 animate-in fade-in slide-in-from-top-2 duration-500">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center">
            <Rocket className="h-4 w-4 text-cyan-400" />
          </div>
          <div>
            <h3 className="text-sm font-black text-white">Activa tu Operación</h3>
            <p className="text-[11px] text-white/30">{completedCount}/{STEPS.length} pasos completados — tu primera victoria en minutos</p>
          </div>
        </div>
        <button onClick={handleDismiss} className="p-1.5 text-white/15 hover:text-white/30 transition-colors">
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* Progress bar */}
      <div className="h-1 bg-white/5 rounded-full mb-4 overflow-hidden">
        <div className="h-full bg-cyan-500 rounded-full transition-all duration-700"
          style={{ width: `${(completedCount / STEPS.length) * 100}%` }} />
      </div>

      {/* Steps */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-2">
        {STEPS.map((step, i) => {
          const Icon = step.icon;
          const done = stepStatus[step.id];
          return (
            <button
              key={step.id}
              onClick={() => !done && router.push(`/${locale}${step.href}`)}
              disabled={done}
              className={`flex items-start gap-3 p-3 rounded-xl text-left transition-all ${
                done
                  ? "bg-emerald-500/5 border border-emerald-500/10 opacity-60"
                  : "bg-white/[0.02] border border-white/5 hover:border-cyan-500/20 hover:bg-cyan-500/[0.03] cursor-pointer"
              }`}
            >
              <div className={`h-7 w-7 rounded-lg flex items-center justify-center shrink-0 mt-0.5 ${
                done ? "bg-emerald-500/10" : "bg-white/5"
              }`}>
                {done ? <CheckCircle2 className="h-4 w-4 text-emerald-400" /> : <Icon className="h-3.5 w-3.5 text-white/30" />}
              </div>
              <div className="min-w-0">
                <p className={`text-xs font-bold ${done ? "text-emerald-400/70 line-through" : "text-white/60"}`}>
                  {step.label}
                </p>
                <p className="text-[10px] text-white/20 mt-0.5 line-clamp-2">{step.desc}</p>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
