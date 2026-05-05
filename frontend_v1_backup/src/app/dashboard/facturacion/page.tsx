"use client";

import { useEffect, useState } from "react";
import { 
  CreditCard, Receipt, DollarSign, Calendar, Download,
  CheckCircle, XCircle, Clock, AlertTriangle, Plus,
  ArrowUpRight, ArrowDownRight, Copy
} from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "https://api.labodegaec.com";

interface Subscription {
  suscripcion: {
    id: string;
    plan: string;
    estado: string;
    monto: number;
    moneda: string;
    periodo: string;
    fecha_inicio: string;
    fecha_proxima_renovacion: string;
  } | null;
  plan: string;
}

interface Invoice {
  id: string;
  numero: string;
  fecha_emision: string;
  fecha_vencimiento: string;
  monto: number;
  estado: string;
}

const PLANES = [
  { id: "starter", nombre: "Starter (Trial)", precio: 0, features: ["Prueba 7 días full", "1000 msgs/día", "3 agentes", "Voz e Imágenes"] },
  { id: "pro", nombre: "Pro", precio: 49, features: ["2 usuarios", "500 msgs/día", "1 agente", "WhatsApp (1)"] },
  { id: "business", nombre: "Business", precio: 99, features: ["5 usuarios", "2500 msgs/día", "3 agentes", "WhatsApp (3)", "Voz"] },
  { id: "enterprise", nombre: "Enterprise", precio: 199, features: ["20 usuarios", "Mensajes ilimitados", "10 agentes", "Multimedia Completa"] },
];

export default function FacturacionPage() {
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [showUpgrade, setShowUpgrade] = useState(false);

  const token = typeof window !== "undefined" ? localStorage.getItem("flux_token") : "";
  const userPlan = typeof window !== "undefined" ? (localStorage.getItem("flux_user_plan") || "starter") : "starter";

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      const [subRes, invRes] = await Promise.all([
        fetch(`${BACKEND_URL}/api/v1/payments/subscription`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
        fetch(`${BACKEND_URL}/api/v1/payments/invoices`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
      ]);

      if (subRes.ok) {
        const subData = await subRes.json();
        setSubscription(subData);
      }

      if (invRes.ok) {
        const invData = await invRes.json();
        setInvoices(invData.facturas || []);
      }
    } catch (e) {
      console.error("Error loading billing:", e);
    } finally {
      setLoading(false);
    }
  }

  const currentPlan = PLANES.find(p => p.id === (subscription?.suscripcion?.plan || userPlan)) || PLANES[0];

  const getStatusBadge = (estado: string) => {
    const configs: Record<string, { bg: string; text: string; icon: any }> = {
      pagada: { bg: "bg-emerald-500/10", text: "text-emerald-400", icon: CheckCircle },
      pendiente: { bg: "bg-amber-500/10", text: "text-amber-400", icon: Clock },
      vencida: { bg: "bg-red-500/10", text: "text-red-400", icon: XCircle },
      cancelada: { bg: "bg-slate-500/10", text: "text-slate-400", icon: AlertTriangle },
    };
    const config = configs[estado] || configs.pendiente;
    const Icon = config.icon;
    
    return (
      <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium ${config.bg} ${config.text}`}>
        <Icon size={12} />
        {estado.charAt(0).toUpperCase() + estado.slice(1)}
      </span>
    );
  };

  return (
    <div className="animate-entry max-w-5xl mx-auto pb-20">
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 24, flexWrap: "wrap", gap: 12 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{ width: 44, height: 44, borderRadius: 12, background: "var(--primary-light)", display: "flex", alignItems: "center", justifyContent: "center", border: "1px solid var(--primary-mid" }}>
            <CreditCard size={22} style={{ color: "var(--primary)" }} />
          </div>
          <div>
            <h1 style={{ fontSize: 24, fontWeight: 800, color: "var(--foreground)", margin: "0 0 8px" }}>
              Facturación y Plan
            </h1>
            <p style={{ fontSize: 14, color: "var(--muted-foreground)", margin: 0 }}>
              Gestiona tu suscripción y método de pago
            </p>
          </div>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 20, marginBottom: 24 }}>
        <Card style={{ padding: 24, background: "var(--card)", border: "1px solid var(--border)", borderRadius: "var(--radius)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 20 }}>
            <div>
              <p style={{ fontSize: 12, color: "var(--muted-foreground)", margin: "0 0 4px" }}>Plan actual</p>
              <h2 style={{ fontSize: 24, fontWeight: 800, color: "var(--foreground)", margin: "0" }}>{currentPlan.nombre}</h2>
            </div>
            <Badge style={{ background: "var(--primary-light)", color: "var(--primary)", border: "none", fontSize: 14, padding: "8px 16px" }}>
              ${currentPlan.precio}/mes
            </Badge>
          </div>

          <div style={{ display: "flex", gap: 16, marginBottom: 20 }}>
            <div style={{ flex: 1, padding: 16, background: "var(--secondary)", borderRadius: 12 }}>
              <p style={{ fontSize: 11, color: "var(--muted-foreground)", margin: "0 0 4px" }}>Próxima facturación</p>
              <p style={{ fontSize: 16, fontWeight: 600, color: "var(--foreground)", margin: 0 }}>
                {subscription?.suscripcion?.fecha_proxima_renovacion 
                  ? new Date(subscription.suscripcion.fecha_proxima_renovacion).toLocaleDateString("es-EC", { day: "numeric", month: "long", year: "numeric" })
                  : "N/A"}
              </p>
            </div>
            <div style={{ flex: 1, padding: 16, background: "var(--secondary)", borderRadius: 12 }}>
              <p style={{ fontSize: 11, color: "var(--muted-foreground)", margin: "0 0 4px" }}>Estado</p>
              <p style={{ fontSize: 16, fontWeight: 600, color: "var(--success)", margin: 0 }}>
                {subscription?.suscripcion?.estado || "Activo"}
              </p>
            </div>
          </div>

          <div>
            <p style={{ fontSize: 12, fontWeight: 600, color: "var(--muted-foreground)", margin: "0 0 12px" }}>Incluye:</p>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
              {currentPlan.features.map((f, i) => (
                <Badge key={i} style={{ background: "var(--secondary)", color: "var(--foreground)", border: "none" }}>
                  <CheckCircle size={12} style={{ marginRight: 4 }} />
                  {f}
                </Badge>
              ))}
            </div>
          </div>
        </Card>

        <Card style={{ padding: 24, background: "var(--card)", border: "1px solid var(--border)", borderRadius: "var(--radius)" }}>
          <h3 style={{ fontSize: 14, fontWeight: 600, color: "var(--foreground)", margin: "0 0 16px" }}>
            Método de pago
          </h3>
          <div style={{ 
            padding: 16, 
            background: "var(--secondary)", 
            borderRadius: 12, 
            display: "flex", 
            alignItems: "center", 
            gap: 12,
            marginBottom: 16
          }}>
            <div style={{ 
              width: 48, height: 32, 
              background: "#009ee3", 
              borderRadius: 4,
              display: "flex", alignItems: "center", justifyContent: "center"
            }}>
              <span style={{ color: "white", fontSize: 10, fontWeight: 700 }}>MP</span>
            </div>
            <div>
              <p style={{ fontSize: 13, fontWeight: 600, color: "var(--foreground)", margin: 0 }}>•••• 4242</p>
              <p style={{ fontSize: 11, color: "var(--muted-foreground)", margin: 0 }}>Expira 12/28</p>
            </div>
          </div>
          <Button variant="outline" style={{ width: "100%" }}>
            Actualizar método de pago
          </Button>
        </Card>
      </div>

      <Card style={{ padding: 24, background: "var(--card)", border: "1px solid var(--border)", borderRadius: "var(--radius)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
          <h3 style={{ fontSize: 16, fontWeight: 700, color: "var(--foreground)", margin: 0 }}>
            <Receipt size={18} style={{ display: "inline", marginRight: 8 }} />
            Historial de Facturas
          </h3>
          <Button variant="outline" size="sm">
            <Download size={14} />
          </Button>
        </div>

        {invoices.length === 0 ? (
          <div style={{ textAlign: "center", padding: 40 }}>
            <Receipt size={32} style={{ color: "var(--muted-foreground)", opacity: 0.5, margin: "0 auto 12px" }} />
            <p style={{ color: "var(--muted-foreground)" }}>No hay facturas disponibles</p>
          </div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ background: "var(--secondary)" }}>
                  <th style={{ padding: "12px 16px", textAlign: "left", fontSize: 11, fontWeight: 600, color: "var(--muted-foreground)", textTransform: "uppercase" }}>Factura</th>
                  <th style={{ padding: "12px 16px", textAlign: "left", fontSize: 11, fontWeight: 600, color: "var(--muted-foreground)", textTransform: "uppercase" }}>Fecha</th>
                  <th style={{ padding: "12px 16px", textAlign: "left", fontSize: 11, fontWeight: 600, color: "var(--muted-foreground)", textTransform: "uppercase" }}>Vencimiento</th>
                  <th style={{ padding: "12px 16px", textAlign: "left", fontSize: 11, fontWeight: 600, color: "var(--muted-foreground)", textTransform: "uppercase" }}>Monto</th>
                  <th style={{ padding: "12px 16px", textAlign: "left", fontSize: 11, fontWeight: 600, color: "var(--muted-foreground)", textTransform: "uppercase" }}>Estado</th>
                  <th style={{ padding: "12px 16px", textAlign: "right", fontSize: 11, fontWeight: 600, color: "var(--muted-foreground)", textTransform: "uppercase" }}>Acción</th>
                </tr>
              </thead>
              <tbody>
                {invoices.map((inv) => (
                  <tr key={inv.id} style={{ borderBottom: "1px solid var(--border)" }}>
                    <td style={{ padding: "16px" }}>
                      <span style={{ fontSize: 13, fontWeight: 600, color: "var(--foreground)" }}>{inv.numero}</span>
                    </td>
                    <td style={{ padding: "16px", fontSize: 13, color: "var(--muted-foreground)" }}>
                      {new Date(inv.fecha_emision).toLocaleDateString("es-EC")}
                    </td>
                    <td style={{ padding: "16px", fontSize: 13, color: "var(--muted-foreground)" }}>
                      {new Date(inv.fecha_vencimiento).toLocaleDateString("es-EC")}
                    </td>
                    <td style={{ padding: "16px" }}>
                      <span style={{ fontSize: 14, fontWeight: 600, color: "var(--foreground)" }}>${inv.monto}</span>
                    </td>
                    <td style={{ padding: "16px" }}>
                      {getStatusBadge(inv.estado)}
                    </td>
                    <td style={{ padding: "16px", textAlign: "right" }}>
                      <Button size="sm" variant="ghost">
                        <Download size={14} />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}