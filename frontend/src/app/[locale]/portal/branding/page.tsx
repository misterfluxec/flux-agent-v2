"use client";

import { useState, useEffect } from "react";
import { 
  Palette, Upload, Globe, Mail, Eye, Save,
  CheckCircle, AlertTriangle
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";

export default function BrandingPage() {
  const [nombreEmpresa, setNombreEmpresa] = useState("Mi Empresa");
  const [colorPrimario, setColorPrimario] = useState("#6366f1");

  useEffect(() => {
    setNombreEmpresa(localStorage.getItem("flux_empresa") || "Mi Empresa");
    setColorPrimario(localStorage.getItem("flux_branding_color") || "#6366f1");
  }, []);
  const [colorSecundario, setColorSecundario] = useState("#8b5cf6");
  const [colorFondo, setColorFondo] = useState("#ffffff");
  const [dominio, setDominio] = useState("");
  const [emailNotificaciones, setEmailNotificaciones] = useState("");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const coloresPresets = [
    "#6366f1", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", 
    "#06b6d4", "#ec4899", "#84cc16", "#f97316", "#6366f1"
  ];

  async function handleSave() {
    setSaving(true);
    localStorage.setItem("flux_empresa", nombreEmpresa);
    localStorage.setItem("flux_branding_color", colorPrimario);
    
    await new Promise(r => setTimeout(r, 1000));
    
    setSaving(false);
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  }

  return (
    <div className="animate-entry max-w-4xl mx-auto pb-20">
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 24, flexWrap: "wrap", gap: 12 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{ width: 44, height: 44, borderRadius: 12, background: "var(--primary-light)", display: "flex", alignItems: "center", justifyContent: "center", border: "1px solid var(--primary-mid" }}>
            <Palette size={22} style={{ color: "var(--primary)" }} />
          </div>
          <div>
            <h1 style={{ fontSize: 24, fontWeight: 800, color: "var(--foreground)", margin: "0 0 8px" }}>
              Branding & Personalización
            </h1>
            <p style={{ fontSize: 14, color: "var(--muted-foreground)", margin: 0 }}>
              Personaliza la apariencia de tu Portal Corporativo
            </p>
          </div>
        </div>
        
        <Button onClick={handleSave} disabled={saving} style={{ background: "var(--primary)", color: "white" }}>
          {saving ? "Guardando..." : saved ? <><CheckCircle size={16} /> Guardado</> : <><Save size={16} /> Guardar cambios</>}
        </Button>
      </div>

      <div style={{ display: "grid", gap: 20 }}>
        <Card style={{ padding: 24, background: "var(--card)", border: "1px solid var(--border)", borderRadius: "var(--radius)" }}>
          <h2 style={{ fontSize: 16, fontWeight: 700, color: "var(--foreground)", margin: "0 0 20px" }}>
            Identidad Visual
          </h2>
          
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 20 }}>
            <div>
              <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "var(--muted-foreground)", marginBottom: 6 }}>Nombre de la empresa</label>
              <Input 
                value={nombreEmpresa} onChange={(e) => setNombreEmpresa(e.target.value)}
                style={{ height: 44 }}
              />
            </div>
            <div>
              <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "var(--muted-foreground)", marginBottom: 6 }}>Color primario</label>
              <div style={{ display: "flex", gap: 8 }}>
                <input 
                  type="color" 
                  value={colorPrimario}
                  onChange={(e) => setColorPrimario(e.target.value)}
                  style={{ width: 44, height: 44, border: "1px solid var(--border)", borderRadius: 8, cursor: "pointer" }}
                />
                <div style={{ flex: 1, display: "flex", gap: 4 }}>
                  {coloresPresets.map(c => (
                    <button
                      key={c}
                      onClick={() => setColorPrimario(c)}
                      style={{
                        width: 28, height: 28,
                        borderRadius: 6,
                        background: c,
                        border: colorPrimario === c ? "2px solid var(--foreground)" : "1px solid var(--border)",
                        cursor: "pointer",
                      }}
                    />
                  ))}
                </div>
              </div>
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
            <div>
              <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "var(--muted-foreground)", marginBottom: 6 }}>Color secundario</label>
              <input 
                type="color" 
                value={colorSecundario}
                onChange={(e) => setColorSecundario(e.target.value)}
                style={{ width: "100%", height: 44, border: "1px solid var(--border)", borderRadius: 8, cursor: "pointer" }}
              />
            </div>
            <div>
              <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "var(--muted-foreground)", marginBottom: 6 }}>Color de fondo</label>
              <input 
                type="color" 
                value={colorFondo}
                onChange={(e) => setColorFondo(e.target.value)}
                style={{ width: "100%", height: 44, border: "1px solid var(--border)", borderRadius: 8, cursor: "pointer" }}
              />
            </div>
          </div>

          <div style={{ marginTop: 20, padding: 16, background: "var(--secondary)", borderRadius: 12 }}>
            <p style={{ fontSize: 12, fontWeight: 600, color: "var(--foreground)", margin: "0 0 12px" }}>Vista previa</p>
            <div style={{ 
              padding: 20, 
              background: colorFondo, 
              borderRadius: 8, 
              border: `2px solid ${colorPrimario}`,
              display: "flex", 
              alignItems: "center", 
              gap: 12 
            }}>
              <div style={{ 
                width: 40, height: 40, 
                borderRadius: 10, 
                background: colorPrimario, 
                display: "flex", alignItems: "center", justifyContent: "center" 
              }}>
                <span style={{ color: "white", fontWeight: 700 }}>{nombreEmpresa.charAt(0).toUpperCase()}</span>
              </div>
              <div>
                <p style={{ fontSize: 14, fontWeight: 700, color: "#1f2937", margin: 0 }}>{nombreEmpresa}</p>
                <p style={{ fontSize: 12, color: "#6b7280", margin: 0 }}>Portal Corporativo</p>
              </div>
            </div>
          </div>
        </Card>

        <Card style={{ padding: 24, background: "var(--card)", border: "1px solid var(--border)", borderRadius: "var(--radius)" }}>
          <h2 style={{ fontSize: 16, fontWeight: 700, color: "var(--foreground)", margin: "0 0 20px" }}>
            <Globe size={18} style={{ display: "inline", marginRight: 8 }} />
            Dominio Personalizado
          </h2>
          
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "var(--muted-foreground)", marginBottom: 6 }}>Dominio personalizado (opcional)</label>
            <Input 
              value={dominio} onChange={(e) => setDominio(e.target.value)}
              placeholder="app.tuempresa.com"
              style={{ height: 44 }}
            />
            <p style={{ fontSize: 11, color: "var(--muted-foreground)", margin: "6px 0 0" }}>
              Configura un CNAME en tu proveedor de DNS pointing to nuestra infraestructura
            </p>
          </div>
        </Card>

        <Card style={{ padding: 24, background: "var(--card)", border: "1px solid var(--border)", borderRadius: "var(--radius)" }}>
          <h2 style={{ fontSize: 16, fontWeight: 700, color: "var(--foreground)", margin: "0 0 20px" }}>
            <Mail size={18} style={{ display: "inline", marginRight: 8 }} />
            Email de Notificaciones
          </h2>
          
          <div>
            <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "var(--muted-foreground)", marginBottom: 6 }}>Email remitente</label>
            <Input 
              value={emailNotificaciones} onChange={(e) => setEmailNotificaciones(e.target.value)}
              placeholder="no-reply@tuempresa.com"
              style={{ height: 44 }}
            />
            <p style={{ fontSize: 11, color: "var(--muted-foreground)", margin: "6px 0 0" }}>
              Este email aparecerá en las notificaciones enviadas a tus clientes
            </p>
          </div>
        </Card>

        <Card style={{ padding: 24, background: "var(--card)", border: "1px solid var(--border)", borderRadius: "var(--radius)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 16 }}>
            <AlertTriangle size={20} style={{ color: "var(--warning)" }} />
            <h2 style={{ fontSize: 16, fontWeight: 700, color: "var(--foreground)", margin: 0 }}>
              Nota Importante
            </h2>
          </div>
          <p style={{ fontSize: 13, color: "var(--muted-foreground)", margin: 0 }}>
            Las cambios de branding están disponibles en el plan Enterprise. 
            Si tienes un plan inferior, los cambios se aplicarán cuando hgaz upgrade.
            El dominio personalizado requiere configuración técnica adicional.
          </p>
        </Card>
      </div>
    </div>
  );
}