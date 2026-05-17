"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import {
  LogOut, Menu, X, ChevronRight, CheckCircle, Circle,
  Sun, Moon, Zap,
  LayoutDashboard, Users, Bot, BookOpen, Package, Link as LinkIcon, TestTube2, Building2,
  Briefcase, FileText, Webhook, Shield, Key, Gauge, Settings
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useTheme } from "next-themes";

const NAV_ITEMS = [
  { href: "/portal", icon: LayoutDashboard, label: "Mi Dashboard", desc: "Resumen ejecutivo" },
  { href: "/portal/leads", icon: Users, label: "Mis Leads", desc: "Oportunidades de venta" },
  { href: "/portal/agentes", icon: Bot, label: "Mis Agentes", desc: "Configurar IA" },
  { href: "/portal/conocimiento", icon: BookOpen, label: "Mi Base de Conocimiento", desc: "Documentos RAG" },
  { href: "/portal/catalogo", icon: Package, label: "Mi Catálogo", desc: "Productos y servicios" },
  { href: "/portal/channels", icon: LinkIcon, label: "Mis Canales", desc: "WhatsApp y más" },
  { href: "/portal/equipo", icon: Briefcase, label: "Mi Equipo", desc: "Usuarios internos" },
  { href: "/portal/reportes", icon: Gauge, label: "Reportes", desc: "Analytics" },
  { href: "/portal/branding", icon: PaletteIcon, label: "Branding", desc: "Personalizar marca" },
  { href: "/portal/seguridad", icon: Shield, label: "Seguridad", desc: "2FA y auditoría" },
  { href: "/portal/api", icon: Key, label: "API & Webhooks", desc: "Integraciones" },
  { href: "/portal/config", icon: Settings, label: "Configuración", desc: "Ajustes generales" },
];

function PaletteIcon(props: any) {
  return (
    <svg {...props} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="13.5" cy="6.5" r=".5" fill="currentColor"/>
      <circle cx="17.5" cy="10.5" r=".5" fill="currentColor"/>
      <circle cx="8.5" cy="7.5" r=".5" fill="currentColor"/>
      <circle cx="6.5" cy="12.5" r=".5" fill="currentColor"/>
      <path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.926 0 1.648-.746 1.648-1.688 0-.437-.18-.835-.437-1.125-.29-.289-.438-.652-.438-1.125a1.64 1.64 0 0 1 1.668-1.668h1.996c3.051 0 5.555-2.503 5.555-5.555C21.965 6.012 17.461 2 12 2z"/>
    </svg>
  )
}

export default function PortalLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { theme, setTheme } = useTheme();
  const [name, setNombre] = useState("");
  const [empresa, setEmpresa] = useState("");
  const [email, setEmail] = useState("");
  const [plan, setPlan] = useState("enterprise");
  const [mobileOpen, setMobileOpen] = useState(false);
  const [brandingColor, setBrandingColor] = useState("#6366f1");

  useEffect(() => {
    const token = localStorage.getItem("flux_token");
    const e = localStorage.getItem("flux_user_email");
    if (!token && !e) { router.replace("/login"); return; }
    setEmail(e ?? "");
    setNombre(localStorage.getItem("flux_user_nombre") ?? (e ?? ""));
    setEmpresa(localStorage.getItem("flux_empresa") ?? "Mi Empresa");
    setPlan(localStorage.getItem("flux_user_plan") ?? "enterprise");
    
    const storedColor = localStorage.getItem("flux_branding_color");
    if (storedColor) setBrandingColor(storedColor);
  }, [router]);

  const logout = useCallback(() => {
    localStorage.clear();
    router.replace("/login");
  }, [router]);

  const activeIdx = NAV_ITEMS.findIndex(
    (n, i) => i === 0
      ? pathname === n.href
      : pathname === n.href || pathname.startsWith(n.href)
  );

  const isDark = theme === "dark";

  return (
    <div style={{ 
      display: "flex", 
      minHeight: "100dvh", 
      background: "var(--background)",
      "--brand-color": brandingColor,
    } as React.CSSProperties}>
      {mobileOpen && (
        <div onClick={() => setMobileOpen(false)}
          style={{ position: "fixed", inset: 0, zIndex: 20, background: "rgba(0,0,0,0.3)", backdropFilter: "blur(2px)" }} />
      )}

      <aside className={cn(
        "fixed top-0 bottom-0 left-0 z-30 flex flex-col transition-transform duration-300 lg:static lg:translate-x-0",
        mobileOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
      )} style={{ 
        width: 270, 
        background: isDark ? "#0f172a" : "#ffffff", 
        borderRight: "1px solid var(--border)",
        boxShadow: "4px 0 20px rgb(0 0 0 / 0.05)" 
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, padding: "0 20px", height: 64, borderBottom: "1px solid var(--border)" }}>
          <div style={{ 
            width: 38, height: 38, 
            borderRadius: 11, 
            background: brandingColor, 
            display: "flex", alignItems: "center", justifyContent: "center", 
            boxShadow: `0 2px 10px ${brandingColor}40`, flexShrink: 0 
          }}>
            <Zap size={18} color="#fff" strokeWidth={2.5} />
          </div>
          <div>
            <p style={{ fontSize: 10, color: "var(--sidebar-muted)", textTransform: "uppercase", letterSpacing: "0.1em", margin: 0 }}>Portal</p>
            <p style={{ fontSize: 15, fontWeight: 800, color: "var(--sidebar-foreground)", margin: 0 }}>{empresa}</p>
          </div>
        </div>

        <nav style={{ flex: 1, padding: "16px 10px", display: "flex", flexDirection: "column", gap: 2, overflowY: "auto" }}>
          {NAV_ITEMS.map((item, idx) => {
            const isActive = idx === activeIdx;
            const isDone = idx < activeIdx && activeIdx > 0;
            return (
              <Link key={item.href} href={item.href} onClick={() => setMobileOpen(false)} style={{ textDecoration: "none" }}>
                <div style={{
                  display: "flex", alignItems: "center", gap: 12,
                  padding: "10px 13px", borderRadius: 10, transition: "all 0.15s",
                  background: isActive ? `${brandingColor}15` : "transparent",
                  border: isActive ? `1px solid ${brandingColor}40` : "1px solid transparent",
                  cursor: "pointer",
                }}>
                  <item.icon 
                    size={19} 
                    strokeWidth={1.5} 
                    style={{ color: isActive ? brandingColor : "var(--sidebar-muted)", flexShrink: 0 }} 
                  />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <p style={{
                      fontSize: 13, fontWeight: isActive ? 600 : 500, margin: 0,
                      color: isActive ? brandingColor : "var(--sidebar-foreground)",
                    }}>{item.label}</p>
                    <p style={{ fontSize: 11, color: "var(--sidebar-muted)", margin: "1px 0 0", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {item.desc}
                    </p>
                  </div>
                  {isActive && <ChevronRight size={14} style={{ color: brandingColor, flexShrink: 0 }} />}
                </div>
              </Link>
            );
          })}
        </nav>

        <div style={{ padding: "14px 16px", borderTop: "1px solid var(--border)", display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{ 
            width: 34, height: 34, 
            borderRadius: "50%", 
            background: `${brandingColor}20`, 
            display: "flex", alignItems: "center", justifyContent: "center", 
            fontSize: 13, fontWeight: 700, color: brandingColor, flexShrink: 0 
          }}>
            {(name || email).charAt(0).toUpperCase() || "A"}
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <p style={{ fontSize: 12, fontWeight: 700, color: "var(--sidebar-foreground)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", margin: 0 }}>
              {name || email}
            </p>
            <p style={{ fontSize: 10, color: "var(--sidebar-muted)", margin: 0 }}>
              <span style={{ textTransform: "capitalize", fontWeight: 600, color: brandingColor }}>{plan}</span>
            </p>
          </div>
          <button onClick={logout} title="Cerrar sesión"
            style={{ padding: 7, borderRadius: 8, border: "none", background: "transparent", cursor: "pointer", color: "var(--sidebar-muted)" }}>
            <LogOut size={15} />
          </button>
        </div>
      </aside>

      <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0, overflow: "hidden" }}>
        <header style={{
          height: 64, display: "flex", alignItems: "center", padding: "0 24px", gap: 12,
          background: "var(--card)", borderBottom: "1px solid var(--border)",
        }}>
          <button onClick={() => setMobileOpen(v => !v)} className="lg:hidden"
            style={{ padding: 8, borderRadius: 8, border: "none", background: "transparent", cursor: "pointer", color: "var(--muted-foreground)" }}>
            {mobileOpen ? <X size={18} /> : <Menu size={18} />}
          </button>

          <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, flex: 1 }}>
            <span style={{ color: "var(--muted-foreground)" }}>{empresa}</span>
            <span style={{ color: "var(--border)" }}>/</span>
            <span style={{ fontWeight: 600, color: "var(--foreground)", display: "flex", alignItems: "center", gap: 6 }}>
              {activeIdx >= 0 && (() => {
                const ActiveIcon = NAV_ITEMS[activeIdx].icon;
                return <ActiveIcon size={16} strokeWidth={2} style={{ color: brandingColor }} />;
              })()}
              {activeIdx >= 0 ? NAV_ITEMS[activeIdx].label : "Dashboard"}
            </span>
          </div>

          <div style={{ flex: 1 }} />

          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <span className="pulse-live" style={{ width: 7, height: 7, borderRadius: "50%", background: brandingColor, display: "inline-block" }} />
            <span style={{ fontSize: 11, fontWeight: 600, color: "var(--muted-foreground)" }}>EN LÍNEA</span>
          </div>

          <button
            onClick={() => setTheme(theme === "light" ? "dark" : "light")}
            style={{
              display: "flex", alignItems: "center", gap: 6,
              padding: "7px 12px", borderRadius: 20,
              border: "1px solid var(--border)",
              background: "var(--secondary)",
              cursor: "pointer", color: "var(--muted-foreground)",
              fontSize: 12, fontWeight: 500,
            }}
          >
            {theme === "light" ? <><Moon size={14} /><span>Oscuro</span></> : <><Sun size={14} /><span>Claro</span></>}
          </button>
        </header>

        <main style={{ flex: 1, overflowY: "auto", padding: "28px" }}>
          {children}
        </main>
      </div>
    </div>
  );
}