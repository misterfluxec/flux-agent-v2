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
  Database,
  Settings,
  ChevronRight,
  AlertCircle,
  CheckCircle2,
  Users,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

// =============================================================================
// CONFIGURACIÓN DEL MENÚ (7 ITEMS MÁXIMO - PRINCIPIO DE JERARQUÍA CLARA)
// =============================================================================

export interface MenuItem {
  id: string;
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  description?: string; // Para tooltips
  badge?: {
    label: string;
    variant?: "default" | "secondary" | "destructive" | "outline";
  };
  children?: Array<{
    label: string;
    href: string;
    description?: string;
  }>;
  requiresPermission?: string; // Para RBAC futuro
}

export const MAIN_MENU_ITEMS: MenuItem[] = [
  {
    id: "dashboard",
    label: "Inicio",
    href: "/dashboard",
    icon: LayoutDashboard,
    description: "Resumen ejecutivo en tiempo real",
  },
  {
    id: "agents",
    label: "Agentes",
    href: "/dashboard/agent",
    icon: Bot,
    description: "Centro operativo IA",
  },
  {
    id: "conversations",
    label: "Conversaciones",
    href: "/dashboard/conversations",
    icon: MessageSquare,
    description: "Inbox inteligente",
  },
  {
    id: "intelligence",
    label: "Inteligencia",
    href: "/dashboard/analytics",
    icon: BarChart3,
    description: "Métricas de alto nivel y consumo",
  },
  {
    id: "channels",
    label: "Canales",
    href: "/dashboard/channels",
    icon: Plug,
    description: "Estado vivo de integraciones",
  },
  {
    id: "team",
    label: "Equipo",
    href: "/dashboard/settings/team",
    icon: Users,
    description: "Roles, usuarios y permisos",
  },
  {
    id: "settings",
    label: "Configuración",
    href: "/dashboard/settings",
    icon: Settings,
    description: "Billing, facturación y sistema",
  },
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

  // Helper para determinar si un item está activo (incluyendo hijos)
  const isItemActive = (item: MenuItem): boolean => {
    if (pathname === item.href) return true;
    if (item.children) {
      return item.children.some((child) => pathname === child.href);
    }
    return false;
  };

  return (
    <aside
      className={cn(
        "flex flex-col h-screen border-r bg-background transition-all duration-200",
        collapsed ? "w-16" : "w-64"
      )}
    >
      {/* Header: Logo + Tenant */}
      <div className={cn("flex items-center gap-3 p-4 border-b", collapsed ? "justify-center" : "")}>
        {!collapsed && (
          <div className="flex-1 min-w-0">
            <h1 className="font-bold text-lg truncate">FluxAgent</h1>
            <p className="text-xs text-muted-foreground truncate">{tenantName}</p>
          </div>
        )}
        {onToggleCollapse && (
          <button
            onClick={onToggleCollapse}
            className={cn(
              "p-1.5 rounded-md hover:bg-muted transition-colors",
              collapsed && "mx-auto"
            )}
            aria-label={collapsed ? "Expandir menú" : "Colapsar menú"}
          >
            <ChevronRight
              className={cn(
                "h-4 w-4 transition-transform",
                collapsed && "rotate-180"
              )}
            />
          </button>
        )}
      </div>

      {/* Navegación principal */}
      <nav className="flex-1 overflow-y-auto py-4">
        <ul className="space-y-1 px-2">
          <TooltipProvider delayDuration={200}>
            {MAIN_MENU_ITEMS.map((item) => {
              const Icon = item.icon;
              const active = isItemActive(item);
              const hasChildren = item.children && item.children.length > 0;

              return (
                <li key={item.id}>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Link
                        href={item.href}
                        className={cn(
                          "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors group",
                          active
                            ? "bg-primary/10 text-primary"
                            : "text-muted-foreground hover:bg-muted hover:text-foreground",
                          collapsed && "justify-center px-2"
                        )}
                      >
                        <Icon
                          className={cn(
                            "h-5 w-5 flex-shrink-0",
                            active && "text-primary"
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
                            {hasChildren && (
                              <ChevronRight className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                            )}
                          </>
                        )}
                      </Link>
                    </TooltipTrigger>
                    {!collapsed && item.description && (
                      <TooltipContent side="right" align="start" className="max-w-xs">
                        <p className="text-sm">{item.description}</p>
                      </TooltipContent>
                    )}
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

                  {/* Submenú expansible (solo cuando no está colapsado) */}
                  {!collapsed && hasChildren && active && (
                    <ul className="ml-9 mt-1 space-y-1 border-l pl-3">
                      {item.children!.map((child) => {
                        const childActive = pathname === child.href;
                        return (
                          <li key={child.href}>
                            <Link
                              href={child.href}
                              className={cn(
                                "block px-3 py-1.5 text-sm rounded-md transition-colors",
                                childActive
                                  ? "text-primary font-medium"
                                  : "text-muted-foreground hover:text-foreground"
                              )}
                            >
                              {child.label}
                            </Link>
                          </li>
                        );
                      })}
                    </ul>
                  )}
                </li>
              );
            })}
          </TooltipProvider>
        </ul>
      </nav>

      {/* Footer: Usuario + Estado del sistema */}
      <div className={cn("p-4 border-t", collapsed ? "flex justify-center" : "")}>
        {!collapsed ? (
          <div className="flex items-center gap-3">
            {userAvatar ? (
              <img
                src={userAvatar}
                alt={userName}
                className="h-8 w-8 rounded-full border"
              />
            ) : (
              <div className="h-8 w-8 rounded-full bg-muted flex items-center justify-center text-xs font-medium">
                {userName.charAt(0).toUpperCase()}
              </div>
            )}
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">{userName}</p>
              <SystemStatusIndicator compact />
            </div>
          </div>
        ) : (
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="relative">
                  {userAvatar ? (
                    <img
                      src={userAvatar}
                      alt={userName}
                      className="h-8 w-8 rounded-full border cursor-pointer"
                    />
                  ) : (
                    <div className="h-8 w-8 rounded-full bg-muted flex items-center justify-center text-xs font-medium cursor-pointer">
                      {userName.charAt(0).toUpperCase()}
                    </div>
                  )}
                  <SystemStatusIndicator compact className="absolute -top-1 -right-1" />
                </div>
              </TooltipTrigger>
              <TooltipContent side="right">
                <p className="font-medium">{userName}</p>
                <SystemStatusIndicator />
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )}
      </div>
    </aside>
  );
}

// =============================================================================
// COMPONENTE AUXILIAR: INDICADOR DE ESTADO DEL SISTEMA
// =============================================================================

/**
 * Muestra el estado de salud del backend (conectado a circuit breakers)
 * Se integra con el endpoint /health que implementamos en Fase 3 backend
 */
function SystemStatusIndicator({
  compact = false,
  className,
}: {
  compact?: boolean;
  className?: string;
}) {
  // TODO: Conectar a query de /health cuando esté disponible
  // Por ahora simulamos estado para demostración
  const systemHealthy = true; // Reemplazar con: useQuery({ queryKey: ['system-health'], ... })

  if (compact) {
    return (
      <div className={cn("flex items-center gap-1", className)}>
        <div
          className={cn(
            "h-2 w-2 rounded-full",
            systemHealthy ? "bg-emerald-500" : "bg-amber-500 animate-pulse"
          )}
        />
      </div>
    );
  }

  return (
    <div className={cn("flex items-center gap-2 text-xs", className)}>
      <div
        className={cn(
          "h-2 w-2 rounded-full",
          systemHealthy ? "bg-emerald-500" : "bg-amber-500 animate-pulse"
        )}
      />
      <span className={systemHealthy ? "text-emerald-600" : "text-amber-600"}>
        {systemHealthy ? "Sistema operativo" : "Mantenimiento"}
      </span>
    </div>
  );
}
