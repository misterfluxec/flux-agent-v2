"use client";

import { FLUX_LEXICON } from "@/constants/lexicon";
import { useTenant } from "@/context/TenantContext";
import { hasFeature, UPGRADE_PROMPTS } from "@/config/flags";
import { useRouter, usePathname } from "next/navigation";
import { ArrowRight, Lock } from "lucide-react";

// =============================================================================
// EMPTY STATE — Progressive Disclosure
// Nunca mostrar una pantalla vacía. Siempre guiar al siguiente paso.
// Ref: docs/specs/COGNITIVE_FLOW_SPEC.md
// =============================================================================

type Module = "operations" | "intelligence" | "workforce" | "flows" | "connectors";

interface EmptyStateProps {
  module: Module;
  actionLabel?: string;
  actionHref?: string;
  gatedFeature?: keyof typeof UPGRADE_PROMPTS;
}

const MODULE_GUIDES: Record<Module, {
  emoji: string; title: string; description: string;
  defaultAction: string; defaultHref: string;
}> = {
  operations: {
    emoji:         "📡",
    title:         `Sin ${FLUX_LEXICON.OPERATIONS} activas`,
    description:   `Conecta un canal para que ${FLUX_LEXICON.YANUA} pueda recibir y atender leads automáticamente.`,
    defaultAction: `🔌 Conectar ${FLUX_LEXICON.CONNECTORS}`,
    defaultHref:   "/dashboard/connectors",
  },
  intelligence: {
    emoji:         "🧠",
    title:         `${FLUX_LEXICON.INTELLIGENCE} sin configurar`,
    description:   `Sube un PDF, URL o catálogo para que tu ${FLUX_LEXICON.WORKFORCE} aprenda sobre tu negocio.`,
    defaultAction: "📤 Subir primer documento",
    defaultHref:   "/dashboard/data-ingestion",
  },
  workforce: {
    emoji:         "🤖",
    title:         `${FLUX_LEXICON.WORKFORCE} sin agentes`,
    description:   `Crea tu primer agente especializado. Dale name, personality y un propósito comercial.`,
    defaultAction: `➕ Crear ${FLUX_LEXICON.AGENT}`,
    defaultHref:   "/dashboard/agents",
  },
  flows: {
    emoji:         "⚡",
    title:         `Sin ${FLUX_LEXICON.FLOWS} configurados`,
    description:   "Define las reglas de automatización: cuándo escalar, cuándo responder, cuándo notificar.",
    defaultAction: "⚡ Crear primer Flujo",
    defaultHref:   "/dashboard/automations",
  },
  connectors: {
    emoji:         "🔌",
    title:         `Sin ${FLUX_LEXICON.CONNECTORS} activos`,
    description:   "Conecta WhatsApp, Web Chat o Telegram para que los leads lleguen a tu operación.",
    defaultAction: "🔌 Conectar Canal",
    defaultHref:   "/dashboard/connectors",
  },
};

export function EmptyState({ module, actionLabel, actionHref, gatedFeature }: EmptyStateProps) {
  const router = useRouter();
  const pathname = usePathname();
  const locale = pathname?.split("/")[1] || "es";
  const { plan } = useTenant();

  const guide = MODULE_GUIDES[module];
  const href = `/${locale}${actionHref ?? guide.defaultHref}`;
  const label = actionLabel ?? guide.defaultAction;
  const isLocked = gatedFeature ? !hasFeature(plan, gatedFeature) : false;

  return (
    <div className="flex flex-col items-center justify-center py-16 px-6 text-center">
      <div className="w-16 h-16 mb-5 bg-white/[0.03] border border-white/[0.06] rounded-2xl flex items-center justify-center text-3xl">
        {guide.emoji}
      </div>
      <h3 className="text-base font-bold text-white/60 mb-2">{guide.title}</h3>
      <p className="text-[13px] text-slate-500 max-w-sm mb-6 leading-relaxed">{guide.description}</p>

      {isLocked ? (
        <div className="space-y-2">
          <div className="flex items-center gap-2 px-4 py-2.5 bg-white/[0.02] border border-white/[0.06] rounded-xl text-[12px] text-slate-500">
            <Lock className="h-3.5 w-3.5" />
            <span>Disponible en Plan Pro</span>
          </div>
          <button onClick={() => router.push(`/${locale}/dashboard/settings?tab=billing`)}
            className="text-[11px] text-cyan-400/60 hover:text-cyan-400 transition-colors flex items-center gap-1 mx-auto">
            {gatedFeature ? UPGRADE_PROMPTS[gatedFeature] : "Ver planes"}
            <ArrowRight className="h-3 w-3" />
          </button>
        </div>
      ) : (
        <button onClick={() => router.push(href)}
          className="flex items-center gap-2 px-5 py-2.5 bg-cyan-500/10 border border-cyan-500/20 text-cyan-300 text-[13px] font-semibold rounded-xl hover:bg-cyan-500/15 transition-all">
          {label}
          <ArrowRight className="h-3.5 w-3.5" />
        </button>
      )}
    </div>
  );
}
