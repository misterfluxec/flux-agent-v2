"use client";

import { useEffect, useState } from "react";
import { 
  TrendingUp, Users, MessageSquare, DollarSign, 
  ArrowUpRight, ArrowDownRight, Zap, Bot, 
  Activity, Clock, CheckCircle, AlertCircle
} from "lucide-react";
import { Card } from "@/components/ui/card";
import { fetchStatsOverview, fetchLeads } from "@/lib/api";

interface KPICardProps {
  title: string;
  value: string | number;
  change?: number;
  icon: React.ReactNode;
  color: string;
}

function KPICard({ title, value, change, icon, color }: KPICardProps) {
  return (
    <Card style={{ 
      padding: "20px", 
      background: "var(--card)", 
      border: "1px solid var(--border)",
      borderRadius: "var(--radius)" 
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 12 }}>
        <div style={{ 
          width: 44, height: 44, 
          borderRadius: 12, 
          background: `${color}15`,
          display: "flex", alignItems: "center", justifyContent: "center",
        }}>
          {icon}
        </div>
        {change !== undefined && (
          <div style={{ 
            display: "flex", alignItems: "center", gap: 4,
            fontSize: 12, fontWeight: 600,
            color: change >= 0 ? "var(--success)" : "var(--destructive)"
          }}>
            {change >= 0 ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
            {Math.abs(change)}%
          </div>
        )}
      </div>
      <p style={{ fontSize: 13, color: "var(--muted-foreground)", margin: "0 0 4px" }}>{title}</p>
      <p style={{ fontSize: 28, fontWeight: 800, color: "var(--foreground)", margin: 0 }}>{value}</p>
    </Card>
  );
}

export default function PortalDashboard() {
  const [stats, setStats] = useState<any>(null);
  const [leads, setLeads] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [empresa, setEmpresa] = useState("");
  const [brandingColor, setBrandingColor] = useState("#6366f1");

  useEffect(() => {
    setEmpresa(localStorage.getItem("flux_empresa") || "Mi Empresa");
    const color = localStorage.getItem("flux_branding_color") || "#6366f1";
    setBrandingColor(color);
    
    loadData();
  }, []);

  async function loadData() {
    try {
      const [statsData, leadsData] = await Promise.all([
        fetchStatsOverview(),
        fetchLeads()
      ]);
      setStats(statsData);
      setLeads(leadsData);
    } catch (e) {
      console.error("Error loading data:", e);
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "50vh" }}>
        <div style={{ textAlign: "center" }}>
          <Zap size={32} style={{ color: brandingColor, animation: "spin 1s linear infinite" }} />
          <p style={{ marginTop: 12, color: "var(--muted-foreground)" }}>Cargando Dashboard...</p>
        </div>
      </div>
    );
  }

  const kpis = stats?.kpis || {};
  const leadsCount = leads.filter(l => l.status === "nuevo" || l.status === "contactado").length;
  const closedCount = leads.filter(l => l.status === "cerrado").length;

  return (
    <div className="animate-entry max-w-7xl mx-auto pb-20">
      <div style={{ marginBottom: 32 }}>
        <h1 style={{ fontSize: 28, fontWeight: 800, color: "var(--foreground)", margin: "0 0 8px" }}>
          Bienvenido a {empresa}
        </h1>
        <p style={{ fontSize: 14, color: "var(--muted-foreground)", margin: 0 }}>
          Este es tu portal corporativo personalizado. Aquí gestionas todo tu negocio.
        </p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 16, marginBottom: 32 }}>
        <KPICard 
          title="Total Conversaciones" 
          value={kpis.total_conversaciones || 0} 
          change={12}
          icon={<MessageSquare size={22} style={{ color: brandingColor }} />}
          color={brandingColor}
        />
        <KPICard 
          title="Leads Activos" 
          value={leadsCount} 
          change={8}
          icon={<Users size={22} style={{ color: "#10b981" }} />}
          color="#10b981"
        />
        <KPICard 
          title="Ventas Cerradas" 
          value={closedCount} 
          change={-3}
          icon={<DollarSign size={22} style={{ color: "#f59e0b" }} />}
          color="#f59e0b"
        />
        <KPICard 
          title="Satisfacción" 
          value={`${Math.round((kpis.sentimiento_promedio || 0.7) * 100)}%`} 
          change={5}
          icon={<TrendingUp size={22} style={{ color: "#6366f1" }} />}
          color="#6366f1"
        />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 20 }}>
        <Card style={{ padding: 20, background: "var(--card)", border: "1px solid var(--border)", borderRadius: "var(--radius)" }}>
          <h3 style={{ fontSize: 16, fontWeight: 700, color: "var(--foreground)", margin: "0 0 16px" }}>
            Conversaciones por Día
          </h3>
          <div style={{ display: "flex", alignItems: "flex-end", gap: 8, height: 150 }}>
            {(stats?.mensajes_por_dia || []).map((day: any, idx: number) => {
              const max = Math.max(...(stats?.mensajes_por_dia || [{conteo: 1}]).map((d: any) => d.conteo), 1);
              const height = (day.conteo / max) * 100;
              return (
                <div key={idx} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: 8 }}>
                  <div style={{ 
                    width: "100%", 
                    height: `${height}%`, 
                    background: brandingColor, 
                    borderRadius: 4,
                    minHeight: 4,
                    transition: "height 0.3s ease"
                  }} />
                  <span style={{ fontSize: 10, color: "var(--muted-foreground)" }}>{day.fecha}</span>
                </div>
              );
            })}
          </div>
        </Card>

        <Card style={{ padding: 20, background: "var(--card)", border: "1px solid var(--border)", borderRadius: "var(--radius)" }}>
          <h3 style={{ fontSize: 16, fontWeight: 700, color: "var(--foreground)", margin: "0 0 16px" }}>
            Estado de Leads
          </h3>
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {[
              { label: "Nuevos", count: leads.filter(l => l.status === "nuevo").length, color: "#6366f1" },
              { label: "Contactados", count: leads.filter(l => l.status === "contactado").length, color: "#10b981" },
              { label: "En negociación", count: leads.filter(l => l.status === "negociacion").length, color: "#f59e0b" },
              { label: "Cerrados", count: leads.filter(l => l.status === "cerrado").length, color: "#8b5cf6" },
            ].map((item, idx) => (
              <div key={idx} style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <div style={{ width: 10, height: 10, borderRadius: 3, background: item.color }} />
                  <span style={{ fontSize: 13, color: "var(--foreground)" }}>{item.label}</span>
                </div>
                <span style={{ fontSize: 14, fontWeight: 700, color: "var(--foreground)" }}>{item.count}</span>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <div style={{ marginTop: 20 }}>
        <Card style={{ padding: 20, background: "var(--card)", border: "1px solid var(--border)", borderRadius: "var(--radius)" }}>
          <h3 style={{ fontSize: 16, fontWeight: 700, color: "var(--foreground)", margin: "0 0 16px" }}>
            Accesos Rápidos
          </h3>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 12 }}>
            {[
              { label: "Nuevo Lead", icon: Users, href: "/portal/leads" },
              { label: "Configurar Agente", icon: Bot, href: "/portal/agentes" },
              { label: "Subir Documentos", icon: Activity, href: "/portal/conocimiento" },
              { label: "Ver Reportes", icon: TrendingUp, href: "/portal/reportes" },
            ].map((item, idx) => (
              <a 
                key={idx} 
                href={item.href}
                style={{ 
                  display: "flex", alignItems: "center", gap: 10,
                  padding: "14px 16px",
                  background: `${brandingColor}10`,
                  border: `1px solid ${brandingColor}30`,
                  borderRadius: 10,
                  textDecoration: "none",
                  color: "var(--foreground)",
                  transition: "all 0.2s",
                }}
              >
                <item.icon size={18} style={{ color: brandingColor }} />
                <span style={{ fontSize: 13, fontWeight: 600 }}>{item.label}</span>
              </a>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}