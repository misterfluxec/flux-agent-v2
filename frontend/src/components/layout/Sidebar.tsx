'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useTranslations, useLocale } from 'next-intl';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  LayoutDashboard, Bot, MessageSquare, Plug, BarChart3, Settings, 
  LogOut, Database, Contact2, Package, TestTube2,
  FileCode2, MessageCircle, FileBarChart, Loader2, ChevronDown, ChevronRight
} from 'lucide-react';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

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
    label: "Panel",
    href: "/dashboard",
    icon: LayoutDashboard,
    description: "Resumen ejecutivo de tu agente IA",
  },
  {
    id: "agent",
    label: "Mi Agente",
    href: "/dashboard/agent",
    icon: Bot,
    description: "Configura identidad, personalidad y conocimiento",
    badge: { label: "Nuevo", variant: "default" }, // Highlight para nueva UX
  },
  {
    id: "conversations",
    label: "Conversaciones",
    href: "/dashboard/conversations",
    icon: MessageSquare,
    description: "Seguimiento de clientes en tiempo real",
  },
  {
    id: "metrics",
    label: "Métricas",
    href: "/dashboard/metrics",
    icon: BarChart3,
    description: "Analytics unificados: rendimiento y ROI",
  },
  {
    id: "channels",
    label: "Canales",
    href: "/dashboard/channels",
    icon: Plug,
    description: "Conecta WhatsApp, Telegram y Web",
  },
  {
    id: "data",
    label: "Datos",
    href: "/dashboard/data",
    icon: Database,
    description: "Alimenta el conocimiento de tu agente",
  },
  {
    id: "settings",
    label: "Configuración",
    href: "/dashboard/settings",
    icon: Settings,
    description: "Facturación, equipo y preferencias",
    children: [
      { label: "General", href: "/dashboard/settings", description: "Preferencias de cuenta" },
      { label: "Facturación", href: "/dashboard/settings/billing", description: "Planes y pagos" },
      { label: "Equipo", href: "/dashboard/settings/team", description: "Gestión de usuarios" },
      { label: "API Keys", href: "/dashboard/settings/api-keys", description: "Acceso programático" },
    ],
  },
];

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
  const [navigatingHref, setNavigatingHref] = useState<string | null>(null);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  
  let t = (key: string) => key;
  let locale = "es";
  try {
    t = useTranslations('navigation');
    locale = useLocale();
  } catch(e) {}


  // Helper para determinar si un item está activo (incluyendo hijos)
  const isItemActive = (item: MenuItem): boolean => {
    if (pathname === item.href) return true;
    if (item.children) {
      return item.children.some((child) => pathname === child.href);
    }
    return false;
  };

  // Reset loading state when pathname changes
  useEffect(() => {
    setNavigatingHref(null);
  }, [pathname]);

  // Verificar si el usuario ha completado el onboarding basado en agentes existentes
  const [onboardingComplete, setOnboardingComplete] = useState(true);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    const checkOnboarding = async () => {
      try {
        const token = localStorage.getItem('flux_token');
        if (!token) {
          setOnboardingComplete(false);
          setLoading(false);
          return;
        }

        const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:9000";
        
        const res = await fetch(`${BACKEND_URL}/api/v1/agents`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (res.ok) {
          const agentsData = await res.json();
          const hasAgents = agentsData && agentsData.length > 0;
          setOnboardingComplete(hasAgents);
          
          // Actualizar localStorage basado en el estado real
          if (typeof window !== 'undefined') {
            if (hasAgents) {
              localStorage.setItem('onboarding_complete', 'true');
              document.cookie = "onboarding_complete=true; path=/; max-age=31536000";
            } else {
              localStorage.removeItem('onboarding_complete');
              document.cookie = "onboarding_complete=; path=/; max-age=0";
            }
          }
        } else {
          setOnboardingComplete(false);
        }
      } catch (error) {
        console.error('Error checking onboarding status:', error);
        setOnboardingComplete(false);
      } finally {
        setLoading(false);
      }
    };
    
    checkOnboarding();
    
    // Escuchar cambios en localStorage
    const handleStorageChange = () => checkOnboarding();
    window.addEventListener('storage', handleStorageChange);
    
    return () => window.removeEventListener('storage', handleStorageChange);
  }, []);

  const renderLinks = (items: any[], isChild = false) => items.map((item) => {
    const isActive = item.href === '/dashboard' 
        ? pathname === '/dashboard' || pathname === `/${locale}/dashboard`
        : pathname.endsWith(item.href);
    
    const hasChildren = item.children && item.children.length > 0;
    const isNavigating = navigatingHref === item.href;

    // Bloquear navegación si el onboarding no está completo o está cargando
    const isBlocked = (!onboardingComplete || loading) && !item.href.includes('/onboarding');
    
    const linkContent = (
      <Link
        href={item.href.startsWith('/') ? `/${locale}${item.href}` : item.href}
        onClick={() => {
          if (isBlocked) {
            // Mostrar tooltip o mensaje de que debe completar onboarding
            return;
          }
          if (hasChildren) {
            setIsSettingsOpen(!isSettingsOpen);
          } else {
            setNavigatingHref(item.href);
          }
        }}
        className={`flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
          isBlocked 
            ? 'opacity-50 cursor-not-allowed text-muted-foreground' 
            : isActive && !isChild
              ? 'bg-primary/10 text-primary' 
              : isChild && isActive
                ? 'text-primary font-bold'
                : 'text-muted-foreground hover:bg-accent hover:text-foreground'
        } ${isChild ? 'ml-9 pl-4 py-1.5 text-xs border-l-2' : ''} ${
          isChild && isActive ? 'border-primary' : isChild ? 'border-transparent' : ''
        } ${isNavigating ? 'opacity-70 grayscale-[0.5]' : ''}`}
      >
        {!isChild && <item.icon className={`w-4 h-4 ${isActive ? 'text-primary' : ''}`} />}
        <span className="flex-1">{t(item.labelKey)}</span>
        
        {isNavigating && <Loader2 className="w-3 h-3 animate-spin text-primary" />}
        
        {item.isNew && (
          <span className="px-1.5 py-0.5 text-[8px] font-black bg-primary text-primary-foreground rounded-full animate-pulse">
            NEW
          </span>
        )}

        {hasChildren && (
          <ChevronDown className={`w-3 h-3 transition-transform duration-200 ${isSettingsOpen ? 'rotate-180' : ''}`} />
        )}
      </Link>
    );

    return (
      <div key={item.href} className="space-y-1">
        {item.hasDesc ? (
          <Tooltip>
            <TooltipTrigger asChild>
              {linkContent}
            </TooltipTrigger>
            <TooltipContent side="right" className="bg-popover text-popover-foreground border-border shadow-xl">
              <p className="text-xs font-medium">{t(`${item.labelKey}_desc` as any)}</p>
            </TooltipContent>
          </Tooltip>
        ) : (
          linkContent
        )}

        {hasChildren && (
          <AnimatePresence>
            {isSettingsOpen && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.2, ease: "easeInOut" }}
                className="overflow-hidden"
              >
                <div className="space-y-1 pb-1">
                  {renderLinks(item.children, true)}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        )}
      </div>
    );
  });

  return (
    <div className="flex flex-col h-full bg-card border-r border-border shadow-sm">
      {/* Logo Area */}
      <div className="h-16 flex items-center px-6 border-b border-border shrink-0">
        <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center mr-3 shadow-lg shadow-primary/20">
          <Bot className="w-5 h-5 text-primary-foreground" />
        </div>
        <span className="text-xl font-black tracking-tight bg-gradient-to-r from-primary to-blue-500 bg-clip-text text-transparent">
          FluxAgent
        </span>
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
        
        <button className="w-full flex items-center gap-3 px-3 py-2 mt-4 text-sm text-red-500 font-bold hover:bg-red-500/10 rounded-md transition-all group">
          <div className="p-1.5 rounded-md bg-red-500/10 group-hover:bg-red-500/20 transition-colors">
            <LogOut className="w-3.5 h-3.5" />
          </div>
          Cerrar Sesión
        </button>
    </div>
  );
}
