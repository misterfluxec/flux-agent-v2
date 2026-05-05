"use client";

import { useEffect, useState, useCallback, useMemo } from "react";
import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import {
  LogOut, Menu, X, ChevronRight, CheckCircle, Circle,
  Sun, Moon, Zap, User, FileText, Plug,
  LayoutDashboard, Users, Bot, BookOpen, Package, Link as LinkIcon,
  TestTube2, Building2, MessageSquare, Briefcase, CreditCard,
  PieChart, Settings, Search, Bell, ChevronLeft, Activity, Sparkles, Lock, Check
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useTheme } from "next-themes";
import { fetchAgents } from "@/lib/api";
import { Button } from "@/components/ui/button";

// ── Navigation por rol ─────────────────────────────────────────────────────────────

const NAV_ITEMS_ADMIN = [
  { href: "/dashboard",              icon: LayoutDashboard, label: "Panel de Ventas",    desc: "Métricas y rendimiento en tiempo real", phase: 0 },
  { href: "/dashboard/agente",       icon: Bot,             label: "Identidad",           desc: "Rol, especialidad y avatar", phase: 0 },
  { href: "/dashboard/script",       icon: FileText,        label: "Estrategia de Ventas",    desc: "Fases, reglas y comportamiento", phase: 1 },
  { href: "/dashboard/centro-de-datos",icon: BookOpen,        label: "Centro de Datos",       desc: "Ingesta y Base de Conocimiento", phase: 2 },
  { href: "/dashboard/inventario",   icon: Package,         label: "Mi Inventario",       desc: "Gestión de productos", phase: 2 },
  { href: "/dashboard/conectores",   icon: Plug,            label: "Conectores",          desc: "Canales de mensajería", phase: 3 },
  { href: "/dashboard/pruebas",      icon: TestTube2,       label: "Centro de Pruebas",   desc: "Simulador y testing", phase: 4 },
  { href: "/dashboard/crm",          icon: Users,           label: "CRM & Leads",         desc: "Gestión de oportunidades", phase: 5 },
  { href: "/dashboard/chat",         icon: MessageSquare,   label: "Chat en Vivo",        desc: "Conversaciones reales", phase: 5 },
  { href: "/dashboard/reportes",     icon: PieChart,        label: "Reportes",            desc: "Analytics y métricas", phase: 5 },
  { href: "/dashboard/equipo",       icon: Briefcase,       label: "Mi Equipo",           desc: "Gestión de usuarios", phase: 5 },
  { href: "/dashboard/facturacion",  icon: CreditCard,      label: "Facturación",         desc: "Plan y pagos", phase: 0 },
  { href: "/dashboard/configuracion",icon: Settings,        label: "Configuración",       desc: "Ajustes del tenant", phase: 0 },
];

const NAV_ITEMS_VIEWER = [
  { href: "/dashboard",              icon: LayoutDashboard, label: "Panel de Ventas",    desc: "Monitorea el rendimiento en tiempo real", phase: 0 },
  { href: "/dashboard/crm",          icon: Users,           label: "CRM & Leads",         desc: "Gestión de oportunidades", phase: 0 },
  { href: "/dashboard/chat",         icon: MessageSquare,   label: "Chat en Vivo",        desc: "Conversaciones", phase: 0 },
  { href: "/dashboard/reportes",     icon: PieChart,        label: "Reportes",            desc: "Analytics y métricas", phase: 0 },
  { href: "/dashboard/inventario",   icon: Package,         label: "Mi Inventario",       desc: "Gestión de productos", phase: 0 },
];

const NAV_ITEMS_AGENTE = [
  { href: "/dashboard/chat",         icon: MessageSquare,   label: "Mis Conversaciones", desc: "Leads asignados", phase: 0 },
  { href: "/dashboard/crm",         icon: Users,           label: "Mis Leads",          desc: "Mis oportunidades", phase: 0 },
  { href: "/dashboard/inventario",   icon: Package,         label: "Mi Catálogo",        desc: "Productos", phase: 0 },
];

// ── Layout ─────────────────────────────────────────────────────────────────

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router   = useRouter();
  const pathname = usePathname();
  const { theme, setTheme } = useTheme();
  
  const [nombre,  setNombre]  = useState("");
  const [empresa, setEmpresa] = useState("");
  const [email,   setEmail]   = useState("");
  const [plan,    setPlan]    = useState("starter");
  const [rol,     setRol]     = useState("admin");
  const [mobileOpen, setMobileOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  
  // Phase management
  const [agentId, setAgentId] = useState<string | null>(null);
  const [currentPhase, setCurrentPhase] = useState(0);

  const calculatePhase = useCallback(() => {
    if (typeof window === "undefined") return 0;
    const hasAgent = !!localStorage.getItem("flux_agent_id");
    if (!hasAgent) return 0;
    
    let phase = 1;
    if (localStorage.getItem("flux_phase_2") === "true") phase = 2;
    if (localStorage.getItem("flux_phase_3") === "true") phase = 3;
    if (localStorage.getItem("flux_phase_4") === "true") phase = 4;
    if (localStorage.getItem("flux_phase_5") === "true") phase = 5;
    return phase;
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const token = localStorage.getItem("flux_token");
    const e     = localStorage.getItem("flux_user_email");
    if (!token && !e) { router.replace("/login"); return; }
    
    setEmail(e ?? "");
    setNombre(localStorage.getItem("flux_user_nombre") ?? (e ?? ""));
    setEmpresa(localStorage.getItem("flux_empresa") ?? "Mi Empresa");
    setPlan(localStorage.getItem("flux_user_plan") ?? "starter");
    setRol(localStorage.getItem("flux_user_rol") ?? "admin");

    // Sync Agent Status
    async function syncAgent() {
      try {
        const agents = await fetchAgents();
        if (agents && agents.length > 0) {
          localStorage.setItem("flux_agent_id", agents[0].id);
          localStorage.setItem("flux_agent_nombre", agents[0].nombre);
          setAgentId(agents[0].id);
          // If agent exists, we are at least phase 1
          if (localStorage.getItem("flux_phase_1") !== "true") {
             localStorage.setItem("flux_phase_1", "true");
          }
        } else {
          localStorage.removeItem("flux_agent_id");
          setAgentId(null);
        }
        setCurrentPhase(calculatePhase());
      } catch (err) {
        console.error("Error syncing agents:", err);
      }
    }
    syncAgent();

    // Listen for localstorage changes (to update phases in real time)
    const handleStorage = () => setCurrentPhase(calculatePhase());
    window.addEventListener('storage', handleStorage);
    return () => window.removeEventListener('storage', handleStorage);
  }, [router, calculatePhase]);

  const logout = useCallback(() => {
    localStorage.clear();
    router.replace("/login");
  }, [router]);

  const NAV_ITEMS = useMemo(() => {
    const items = (rol === "admin" || rol === "super_admin") ? NAV_ITEMS_ADMIN 
      : rol === "viewer" ? NAV_ITEMS_VIEWER 
      : NAV_ITEMS_AGENTE;
    return items;
  }, [rol]);

  const activeIdx = NAV_ITEMS.findIndex(
    (n, i) => i === 0
      ? pathname === n.href
      : pathname === n.href || pathname.startsWith(n.href)
  );

  const phaseMessages: Record<number, string> = {
    1: "📜 Paso 2 de 5: Escríbele el guión de ventas a tu agente",
    2: "🗄️ Paso 3 de 5: Alimenta a tu agente con conocimiento",
    3: "🔌 Paso 4 de 5: Conéctalo a un canal de mensajería",
    4: "🧪 Paso 5 de 5: Realiza tu primera prueba del sistema",
  };

  const phaseLinks: Record<number, string> = {
    1: "/dashboard/script",
    2: "/dashboard/centro-de-datos",
    3: "/dashboard/conectores",
    4: "/dashboard/pruebas",
  };

  const currentPathLocked = useMemo(() => {
    const currentItem = NAV_ITEMS.find(n => 
      n.href === "/dashboard" 
        ? pathname === n.href 
        : pathname.startsWith(n.href)
    );
    return currentItem ? itemLocked(currentItem.phase, currentPhase) : false;

    function itemLocked(itemPhase: number, userPhase: number) {
      if (itemPhase === 0) return false;
      return itemPhase > userPhase;
    }
  }, [pathname, currentPhase, NAV_ITEMS]);

  return (
    <div 
      style={{ display: "flex", minHeight: "100dvh", background: "var(--background)" }}
      suppressHydrationWarning
    >
      {/* Mobile overlay */}
      {mobileOpen && (
        <div onClick={() => setMobileOpen(false)}
          style={{ position: "fixed", inset: 0, zIndex: 50, background: "rgba(0,0,0,0.3)", backdropFilter: "blur(2px)" }} />
      )}

      {/* ══ SIDEBAR ══════════════════════════════════════════════════ */}
      <aside className={cn(
        "fixed top-0 bottom-0 left-0 z-40 flex flex-col transition-all duration-300 lg:static lg:translate-x-0",
        mobileOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
      )} style={{ width: sidebarCollapsed ? 80 : 256, background: "var(--sidebar)", borderRight: "1px solid var(--sidebar-border)", boxShadow: "4px 0 20px rgb(0 0 0 / 0.05)" }}>

        {/* Logo */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: sidebarCollapsed ? "center" : "flex-start", gap: 12, padding: sidebarCollapsed ? "0" : "0 20px", height: 64, borderBottom: "1px solid var(--sidebar-border)" }}>
          <div style={{ width: 38, height: 38, borderRadius: 11, background: "var(--primary)", display: "flex", alignItems: "center", justifyContent: "center", boxShadow: "0 2px 10px var(--primary)40", flexShrink: 0 }}>
            <Zap size={18} color="#fff" strokeWidth={2.5} />
          </div>
          {!sidebarCollapsed && (
            <div className="overflow-hidden whitespace-nowrap transition-all duration-300">
              <p style={{ fontSize: 10, color: "var(--sidebar-muted)", textTransform: "uppercase", letterSpacing: "0.1em", margin: 0 }}>Panel de Control</p>
              <p style={{ fontSize: 15, fontWeight: 800, color: "var(--sidebar-foreground)", margin: 0 }}>Yanua AI</p>
            </div>
          )}
        </div>

        {/* Nav */}
        <nav style={{ flex: 1, padding: "16px 10px", display: "flex", flexDirection: "column", gap: 3, overflowY: "auto" }}>
          {NAV_ITEMS.map((item, idx) => {
            const isActive = idx === activeIdx;
            const isBlocked = item.phase > currentPhase;
            const isCompleted = item.phase < currentPhase && item.phase !== 0;

            return (
              <Link 
                key={item.href} 
                href={isBlocked ? "#" : item.href} 
                onClick={(e) => {
                  if (isBlocked) {
                    e.preventDefault();
                    toast.info(`Desbloquea esta sección completando la fase ${item.phase}`);
                  } else {
                    setMobileOpen(false);
                  }
                }} 
                style={{ textDecoration: "none" }}
              >
                <div style={{
                  display: "flex", alignItems: "center", justifyContent: sidebarCollapsed ? "center" : "flex-start", gap: 12,
                  padding: sidebarCollapsed ? "11px 0" : "11px 13px", borderRadius: 11, transition: "all 0.15s",
                  background: isActive ? "var(--sidebar-accent)" : "transparent",
                  border: isActive ? "1px solid var(--primary-mid)" : "1px solid transparent",
                  opacity: isBlocked ? 0.4 : 1,
                  cursor: isBlocked ? "not-allowed" : "pointer",
                }} title={isBlocked ? `Fase ${item.phase} requerida` : sidebarCollapsed ? item.label : undefined}>
                  {/* Icon */}
                  <div className="relative">
                    <item.icon 
                      size={20} 
                      strokeWidth={1.5} 
                      className={isActive ? "text-indigo-600 dark:text-indigo-400" : "text-slate-500 dark:text-slate-400"} 
                      style={{ flexShrink: 0 }} 
                    />
                    {isBlocked && !sidebarCollapsed && (
                      <div className="absolute -top-1 -right-1 bg-slate-900 rounded-full p-0.5 border border-slate-700">
                        <Lock size={8} className="text-slate-500" />
                      </div>
                    )}
                  </div>

                  {!sidebarCollapsed && (
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div className="flex items-center justify-between gap-2">
                        <p style={{
                          fontSize: 13, fontWeight: isActive ? 700 : 500, margin: 0,
                          color: isActive ? "var(--sidebar-primary)" : "var(--sidebar-foreground)",
                        }}>{item.label}</p>
                        {isCompleted && <Check size={12} className="text-emerald-500" />}
                      </div>
                      <p style={{ fontSize: 11, color: "var(--sidebar-muted)", margin: "1px 0 0", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                        {isBlocked ? `Requiere Fase ${item.phase}` : item.desc}
                      </p>
                    </div>
                  )}

                  {!sidebarCollapsed && isActive && <ChevronRight size={14} style={{ color: "var(--sidebar-primary)", flexShrink: 0 }} />}
                </div>
              </Link>
            );
          })}
        </nav>

        {/* User strip & Toggle */}
        <div style={{ padding: sidebarCollapsed ? "14px 0" : "14px 16px", borderTop: "1px solid var(--sidebar-border)", display: "flex", flexDirection: sidebarCollapsed ? "column" : "row", alignItems: "center", gap: 10 }}>
          <div style={{ width: 34, height: 34, borderRadius: "50%", background: "var(--sidebar-accent)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 13, fontWeight: 700, color: "var(--sidebar-primary)", flexShrink: 0 }}>
            {(nombre || email).charAt(0).toUpperCase() || "A"}
          </div>
          {!sidebarCollapsed && (
            <div style={{ flex: 1, minWidth: 0 }}>
              <p style={{ fontSize: 12, fontWeight: 700, color: "var(--sidebar-foreground)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", margin: 0 }}>
                {nombre || email}
              </p>
              <p style={{ fontSize: 10, color: "var(--sidebar-muted)", margin: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                {empresa} &middot; <span style={{ textTransform: "capitalize", fontWeight: 600, color: "var(--primary)" }}>{plan}</span>
              </p>
            </div>
          )}
          <div style={{ display: "flex", flexDirection: sidebarCollapsed ? "column" : "row", gap: 8 }}>
            <button onClick={() => setSidebarCollapsed(!sidebarCollapsed)} title="Contraer/Expandir menú"
              className="hidden lg:flex"
              style={{ padding: 7, borderRadius: 8, border: "none", background: "transparent", cursor: "pointer", color: "var(--sidebar-muted)", transition: "background 0.15s", alignItems: "center", justifyContent: "center" }}
              onMouseEnter={e => (e.currentTarget.style.background = "var(--secondary)")}
              onMouseLeave={e => (e.currentTarget.style.background = "transparent")}>
              {sidebarCollapsed ? <ChevronRight size={15} /> : <ChevronLeft size={15} />}
            </button>
            <button onClick={logout} title="Cerrar sesión"
              style={{ padding: 7, borderRadius: 8, border: "none", background: "transparent", cursor: "pointer", color: "var(--sidebar-muted)", transition: "background 0.15s", display: "flex", alignItems: "center", justifyContent: "center" }}
              onMouseEnter={e => (e.currentTarget.style.background = "var(--secondary)")}
              onMouseLeave={e => (e.currentTarget.style.background = "transparent")}>
              <LogOut size={15} />
            </button>
          </div>
        </div>
      </aside>

      {/* ══ MAIN ═════════════════════════════════════════════════════ */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0, overflow: "hidden" }}>

        {/* Topbar */}
        <header style={{
          position: "sticky", top: 0, zIndex: 30,
          height: 64, display: "flex", alignItems: "center", padding: "0 24px", gap: 16,
          background: "var(--card)", borderBottom: "1px solid var(--border)",
          boxShadow: "var(--shadow-sm)", flexShrink: 0,
        }}>
          {/* Mobile toggle */}
          <button onClick={() => setMobileOpen(v => !v)} className="lg:hidden"
            style={{ padding: 8, borderRadius: 8, border: "none", background: "transparent", cursor: "pointer", color: "var(--muted-foreground)" }}>
            {mobileOpen ? <X size={18} /> : <Menu size={18} />}
          </button>

          {/* Logo / Business Name in Topbar */}
          <div className="hidden md:flex items-center gap-3 flex-1">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white shadow-lg">
              <Sparkles className="w-4 h-4" />
            </div>
            <span className="font-bold text-lg text-slate-800 dark:text-slate-100 tracking-tight">
              {empresa || "VentaCore AI"}
            </span>
          </div>

          {/* Spacer for mobile */}
          <div className="flex-1 md:hidden" />

          {/* Uptime and Status */}
          <div className="hidden sm:flex items-center gap-3 text-sm px-3 py-1.5 rounded-full bg-slate-50 dark:bg-slate-900 border border-border">
            <div className="flex items-center gap-1.5">
              <span className="status-dot online" />
              <span className="font-medium text-slate-700 dark:text-slate-300">Online</span>
            </div>
            <div className="w-px h-4 bg-border" />
            <div className="flex items-center gap-1.5">
              <Activity size={14} className="text-emerald-500" />
              <span className="font-semibold text-slate-700 dark:text-slate-300">98.5% <span className="font-normal text-slate-500">uptime</span></span>
            </div>
          </div>

          {/* Notifications */}
          <button className="relative p-2 text-slate-500 hover:text-foreground transition-colors">
            <Bell size={20} />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-pink-500 rounded-full" />
          </button>

          {/* Settings Shortcut */}
          <button className="p-2 text-slate-500 hover:text-foreground transition-colors hidden sm:block">
            <Settings size={20} />
          </button>

          {/* Avatar Menu */}
          <div className="relative group">
            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center text-white font-bold text-sm shadow-sm cursor-pointer hover:shadow-md transition-shadow">
              {nombre ? nombre.substring(0, 2).toUpperCase() : 'CA'}
            </div>
            {/* Dropdown Menu */}
            <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-slate-800 rounded-xl shadow-lg border border-border opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all transform origin-top-right z-50">
              <div className="p-3 border-b border-border">
                <p className="text-sm font-medium">{nombre || 'Usuario'}</p>
                <p className="text-xs text-muted-foreground truncate">{email}</p>
              </div>
              <div className="p-1">
                <button
                  onClick={logout}
                  className="w-full text-left px-3 py-2 text-sm text-red-500 hover:bg-red-500/10 rounded-lg transition-colors flex items-center gap-2"
                >
                  <LogOut size={14} />
                  Cerrar sesión
                </button>
              </div>
            </div>
          </div>
        </header>

        {/* Phase Progress Banner */}
        {currentPhase > 0 && currentPhase < 5 && phaseMessages[currentPhase] && (
          <div className="bg-indigo-600 px-6 py-2 flex items-center justify-between text-white animate-in slide-in-from-top duration-500 z-20 shadow-lg">
            <p className="text-sm font-bold flex items-center gap-2">
              <Sparkles size={16} className="animate-pulse" />
              {phaseMessages[currentPhase]}
            </p>
            <Link href={phaseLinks[currentPhase]} className="bg-white/20 hover:bg-white/30 px-4 py-1 rounded-full text-xs font-bold transition-all backdrop-blur-md border border-white/30">
              Continuar →
            </Link>
          </div>
        )}

        {/* Content */}
        <main style={{ flex: 1, overflowY: "auto", padding: "28px" }} className="bg-slate-50/50 dark:bg-slate-950/50">
          {currentPathLocked ? (
            <div className="flex flex-col items-center justify-center h-full text-center p-8 animate-in fade-in zoom-in duration-300">
              <div className="w-24 h-24 bg-white dark:bg-slate-900 rounded-[2rem] flex items-center justify-center mb-8 border border-border shadow-2xl relative">
                <div className="absolute inset-0 bg-indigo-500/10 blur-2xl rounded-full" />
                <Lock className="w-10 h-10 text-indigo-500 relative z-10" />
              </div>
              <h2 className="text-3xl font-extrabold mb-3 tracking-tight">Acceso Restringido</h2>
              <p className="text-slate-500 dark:text-slate-400 max-w-sm mb-10 text-lg leading-relaxed">
                Esta sección se desbloqueará automáticamente cuando tu FluxBot complete la <span className="font-bold text-indigo-500 text-nowrap">Fase {currentPhase + 1}</span> de entrenamiento.
              </p>
              <Button 
                onClick={() => router.push(phaseLinks[currentPhase] || "/dashboard")}
                className="rounded-2xl px-10 h-14 text-lg font-bold bg-indigo-600 hover:bg-indigo-700 shadow-xl shadow-indigo-500/20 transition-all hover:scale-105 active:scale-95"
              >
                Continuar Entrenamiento
              </Button>
            </div>
          ) : children}
        </main>
      </div>
      
      <style jsx global>{`
        .status-dot { width: 8px; height: 8px; border-radius: 50%; }
        .status-dot.online { background: #10b981; box-shadow: 0 0 10px #10b98144; animation: pulse-green 2s infinite; }
        @keyframes pulse-green {
          0% { transform: scale(1); opacity: 1; }
          50% { transform: scale(1.2); opacity: 0.7; }
          100% { transform: scale(1); opacity: 1; }
        }
      `}</style>
    </div>
  );
}

import { toast } from "sonner";
