"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  Bot,
  MessageSquare,
  BarChart3,
  Plug,
  Brain,
  ChevronRight,
  Building2,
  Zap,
  Users2,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

// =============================================================================
// TIPOS
// =============================================================================

export interface MenuItem {
  id: string;
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  description?: string;
  badge?: {
    label: string;
    variant?: "default" | "secondary" | "destructive" | "outline";
  };
  children?: Array<{
    label: string;
    href: string;
    description?: string;
  }>;
  requiresPermission?: string;
}

interface MenuSection {
  id: string;
  label: string;
  items: MenuItem[];
}

// =============================================================================
// ARQUITECTURA DE NAVEGACIÓN DEFINITIVA
// Estructura cognitiva: OPERAR → CONFIGURAR → ANALIZAR → EMPRESA
// =============================================================================

export const MENU_SECTIONS: MenuSection[] = [
  {
    id: "operate",
    label: "OPERAR",
    items: [
      {
        id: "dashboard",
        label: "Control",
        href: "/dashboard",
        icon: LayoutDashboard,
        description: "Torre de control — Estado global y prioridades",
      },
      {
        id: "operations",
        label: "Operaciones",
        href: "/dashboard/operations",
        icon: MessageSquare,
        description: "Mission Control — Timeline, Colas y Acciones",
      },
      {
        id: "conversations",
        label: "Conversaciones",
        href: "/dashboard/conversations",
        icon: MessageSquare,
        description: "Inbox, leads y handoffs",
      },
    ],
  },
  {
    id: "configure",
    label: "CONFIGURAR",
    items: [
      {
        id: "agents",
        label: "Agentes IA",
        href: "/dashboard/agents",
        icon: Users2,
        description: "Workforce multi-agente — Crear, configurar y supervisar",
      },
      {
        id: "intelligence",
        label: "Inteligencia",
        href: "/dashboard/data-ingestion",
        icon: Brain,
        description: "Aprender → Procesar → Validar → Asignar",
      },
      {
        id: "channels",
        label: "Canales",
        href: "/dashboard/connectors",
        icon: Plug,
        description: "WhatsApp, Telegram, Web — Estado vivo y reconexión",
      },
      {
        id: "flows",
        label: "Flujos",
        href: "/dashboard/automations",
        icon: Zap,
        description: "Reglas y automatizaciones del Policy Engine",
      },
    ],
  },
  {
    id: "analyze",
    label: "ANALIZAR",
    items: [
      {
        id: "results",
        label: "Resultados",
        href: "/dashboard/analytics",
        icon: BarChart3,
        description: "KPIs accionables — Conversión, ROI, consumo",
      },
    ],
  },
];

// Item fijo del footer (fuera de secciones)
export const FOOTER_MENU_ITEM: MenuItem = {
  id: "organization",
  label: "Organización",
  href: "/dashboard/settings",
  icon: Building2,
  description: "Empresa, equipo, facturación y seguridad",
};

// Flat list para compatibilidad (incluye todos los items + footer)
export const MAIN_MENU_ITEMS: MenuItem[] = [
  ...MENU_SECTIONS.flatMap(s => s.items),
  FOOTER_MENU_ITEM,
];

// =============================================================================
// COMPONENTE PRINCIPAL: SIDEBAR
// =============================================================================

interface SidebarProps {
  collapsed?: boolean;
  onToggleCollapse?: () => void;
  tenantName?: string;
  userAvatar?: string;
  userName?: string;
}

export function Sidebar({
  collapsed = false,
  onToggleCollapse,
  tenantName = "Mi Empresa",
  userAvatar,
  userName = "Usuario",
}: SidebarProps) {
  const pathname = usePathname();

  const isItemActive = (item: MenuItem): boolean => {
    // Exact match
    if (pathname.endsWith(item.href)) return true;
    // Prefix match for sub-routes (e.g. /dashboard/agents/xxx)
    if (item.href !== "/dashboard" && pathname.includes(item.href)) return true;
    // Children match
    if (item.children) {
      return item.children.some((child) => pathname.endsWith(child.href));
    }
    return false;
  };

  const renderMenuItem = (item: MenuItem) => {
    const Icon = item.icon;
    const active = isItemActive(item);

    return (
      <li key={item.id}>
        <Tooltip>
          <TooltipTrigger asChild>
            <Link
              href={item.href}
              className={cn(
                // Base: 13px mínimo, sin shrink-0 agresivo
                "flex items-center gap-3 px-3 py-2 rounded-xl transition-all duration-150 group",
                "text-[13px] font-medium",
                active
                  // Activo: borde + fondo muy sutil. Sin glow para no fatigar
                  ? "bg-cyan-500/[0.08] text-cyan-300/90 border border-cyan-500/[0.12]"
                  // Inactivo: texto slate-400 (legible sin brillar)
                  : "text-slate-400 hover:bg-white/[0.04] hover:text-slate-200 border border-transparent",
                collapsed && "justify-center px-2"
              )}
            >
              <Icon
                className={cn(
                  "h-[17px] w-[17px] flex-shrink-0 transition-colors",
                  // Icono is_active: cyan suave. Inactivo: muy discreto
                  active ? "text-cyan-400/80" : "text-slate-500 group-hover:text-slate-300"
                )}
              />
              {!collapsed && (
                <>
                  <span className="flex-1 truncate">{item.label}</span>
                  {item.badge && (
                    <Badge
                      variant={item.badge.variant}
                      className="text-[10px] px-1.5 py-0 h-5"
                    >
                      {item.badge.label}
                    </Badge>
                  )}
                </>
              )}
            </Link>
          </TooltipTrigger>
          {collapsed && (
            <TooltipContent side="right" className="max-w-xs">
              <p className="font-medium">{item.label}</p>
              {item.description && (
                <p className="text-xs text-muted-foreground mt-1">
                  {item.description}
                </p>
              )}
            </TooltipContent>
          )}
        </Tooltip>
      </li>
    );
  };

  return (
    <aside
      className={cn(
        // Sidebar: bg más neutro, borde más sutil
        "flex flex-col h-screen border-r border-white/[0.04] bg-[#080c14] text-white transition-all duration-300",
        collapsed ? "w-[72px]" : "w-60"
      )}
    >
      {/* Header: Logo + Tenant */}
      <div className={cn("flex items-center gap-3 px-5 py-5 border-b border-white/5", collapsed ? "justify-center px-3" : "")}>
        {!collapsed && (
          <div className="flex-1 min-w-0">
            <h1 className="font-black text-lg tracking-tight text-white flex items-center gap-2">
              FluxAgent <span className="text-cyan-400 text-[10px] font-bold bg-cyan-400/10 px-1.5 py-0.5 rounded tracking-widest">OS</span>
            </h1>
            <p className="text-[11px] text-white/30 font-medium truncate mt-0.5">{tenantName}</p>
          </div>
        )}
        {onToggleCollapse && (
          <button
            onClick={onToggleCollapse}
            className={cn(
              "p-1.5 rounded-md hover:bg-white/5 transition-colors",
              collapsed && "mx-auto"
            )}
            aria-label={collapsed ? "Expandir menú" : "Colapsar menú"}
          >
            <ChevronRight
              className={cn(
                "h-4 w-4 text-white/30 transition-transform",
                !collapsed && "rotate-180"
              )}
            />
          </button>
        )}
      </div>

      {/* Navegación por secciones cognitivas */}
      <nav className="flex-1 overflow-y-auto py-3">
        <TooltipProvider delayDuration={200}>
          {MENU_SECTIONS.map((section, sectionIndex) => (
            <div key={section.id} className={cn(sectionIndex > 0 && "mt-4")}>
              {/* Section Label — más legible: 10px tracking estricto */}
              {!collapsed && (
                <p className="px-4 mb-1.5 text-[10px] font-bold uppercase tracking-[0.12em] text-slate-600">
                  {section.label}
                </p>
              )}
              {collapsed && sectionIndex > 0 && (
                <div className="mx-4 mb-2 border-t border-white/5" />
              )}
              <ul className="space-y-0.5 px-2">
                {section.items.map(renderMenuItem)}
              </ul>
            </div>
          ))}
        </TooltipProvider>
      </nav>

      {/* Footer: Organización + Usuario */}
      <div className={cn("border-t border-white/5 bg-black/40", collapsed ? "px-2 py-3" : "p-4")}>
        {/* Organización link */}
        <TooltipProvider delayDuration={200}>
          <div className="mb-3">
            {renderMenuItem(FOOTER_MENU_ITEM)}
          </div>
        </TooltipProvider>

        {/* User info */}
        {!collapsed ? (
          <div className="flex items-center gap-3 px-2">
            {userAvatar ? (
              <img
                src={userAvatar}
                alt={userName}
                className="h-8 w-8 rounded-full border border-white/10"
              />
            ) : (
              <div className="h-8 w-8 rounded-full bg-white/5 border border-white/10 flex items-center justify-center text-xs font-bold text-white/60">
                {userName.charAt(0).toUpperCase()}
              </div>
            )}
            <div className="flex-1 min-w-0">
              {/* Username: 13px, legible */}
              <p className="text-[13px] font-semibold text-slate-300 truncate">{userName}</p>
              <div className="flex items-center gap-1.5 mt-0.5">
                {/* Dot sin animación — el verde siempre encendido no fatiga */}
                <div className="h-1.5 w-1.5 rounded-full bg-emerald-500/70" />
                <span className="text-[11px] text-slate-600">En línea</span>
              </div>
            </div>
          </div>
        ) : (
          <Tooltip>
            <TooltipTrigger asChild>
              <div className="flex justify-center">
                {userAvatar ? (
                  <img
                    src={userAvatar}
                    alt={userName}
                    className="h-8 w-8 rounded-full border border-white/10 cursor-pointer"
                  />
                ) : (
                  <div className="h-8 w-8 rounded-full bg-white/5 border border-white/10 flex items-center justify-center text-xs font-bold text-white/60 cursor-pointer">
                    {userName.charAt(0).toUpperCase()}
                  </div>
                )}
              </div>
            </TooltipTrigger>
            <TooltipContent side="right">
              <p className="font-medium">{userName}</p>
              <p className="text-xs text-emerald-400">En línea</p>
            </TooltipContent>
          </Tooltip>
        )}
      </div>
    </aside>
  );
}
