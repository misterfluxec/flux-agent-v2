"use client";

import { useState } from "react";
import { 
  Shield, Lock, Key, Smartphone, Eye, EyeOff, 
  CheckCircle, XCircle, AlertTriangle, Users, Clock,
  Download, RefreshCw
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export default function SeguridadPage() {
  const [twoFactorEnabled, setTwoFactorEnabled] = useState(false);
  const [ipWhitelistEnabled, setIpWhitelistEnabled] = useState(false);
  const [ipWhitelist, setIpWhitelist] = useState("");
  const [passwordMinLength, setPasswordMinLength] = useState(8);
  const [passwordRequireSpecial, setPasswordRequireSpecial] = useState(true);
  const [passwordRequireNumber, setPasswordRequireNumber] = useState(true);
  const [sessionTimeout, setSessionTimeout] = useState(60);
  const [retentionDays, setRetentionDays] = useState(90);
  const [saving, setSaving] = useState(false);

  const sesionesActivas = [
    { id: "1", dispositivo: "Chrome - Windows", ubicacion: "Quito, Ecuador", ultimaActividad: "Ahora", actual: true },
    { id: "2", dispositivo: "Safari - iPhone", ubicacion: "Guayaquil, Ecuador", ultimaActividad: "Hace 2 horas", actual: false },
  ];

  async function handleSave() {
    setSaving(true);
    await new Promise(r => setTimeout(r, 1000));
    setSaving(false);
  }

  return (
    <div className="animate-entry max-w-4xl mx-auto pb-20">
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 24 }}>
        <div style={{ width: 44, height: 44, borderRadius: 12, background: "var(--primary-light)", display: "flex", alignItems: "center", justifyContent: "center", border: "1px solid var(--primary-mid" }}>
          <Shield size={22} style={{ color: "var(--primary)" }} />
        </div>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 800, color: "var(--foreground)", margin: "0 0 8px" }}>
            Seguridad Enterprise
          </h1>
          <p style={{ fontSize: 14, color: "var(--muted-foreground)", margin: 0 }}>
            Configura políticas de seguridad avanzadas para tu organización
          </p>
        </div>
      </div>

      <div style={{ display: "grid", gap: 20 }}>
        <Card style={{ padding: 24, background: "var(--card)", border: "1px solid var(--border)", borderRadius: "var(--radius)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
            <div>
              <h2 style={{ fontSize: 16, fontWeight: 700, color: "var(--foreground)", margin: "0 0 4px" }}>
                <Smartphone size={18} style={{ display: "inline", marginRight: 8 }} />
                Autenticación de Dos Factores (2FA)
              </h2>
              <p style={{ fontSize: 13, color: "var(--muted-foreground)", margin: 0 }}>
                Obliga a todos los usuarios a usar 2FA para iniciar sesión
              </p>
            </div>
            <button
              onClick={() => setTwoFactorEnabled(!twoFactorEnabled)}
              style={{
                width: 48, height: 28, borderRadius: 14,
                background: twoFactorEnabled ? "var(--primary)" : "var(--border)",
                border: "none",
                cursor: "pointer",
                position: "relative",
                transition: "background 0.2s",
              }}
            >
              <div style={{
                width: 24, height: 24, borderRadius: "50%",
                background: "white",
                position: "absolute",
                top: 2,
                left: twoFactorEnabled ? 22 : 2,
                transition: "left 0.2s",
              }} />
            </button>
          </div>
          
          {twoFactorEnabled && (
            <div style={{ padding: 16, background: "var(--secondary)", borderRadius: 12 }}>
              <p style={{ fontSize: 13, color: "var(--success)", margin: 0, display: "flex", alignItems: "center", gap: 8 }}>
                <CheckCircle size={16} />
                2FA obligatorio está habilitado para todos los usuarios
              </p>
            </div>
          )}
        </Card>

        <Card style={{ padding: 24, background: "var(--card)", border: "1px solid var(--border)", borderRadius: "var(--radius)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
            <div>
              <h2 style={{ fontSize: 16, fontWeight: 700, color: "var(--foreground)", margin: "0 0 4px" }}>
                <Key size={18} style={{ display: "inline", marginRight: 8 }} />
                Lista de IPs Permitidas (Whitelist)
              </h2>
              <p style={{ fontSize: 13, color: "var(--muted-foreground)", margin: 0 }}>
                Restringe el acceso solo a IPs específicas
              </p>
            </div>
            <button
              onClick={() => setIpWhitelistEnabled(!ipWhitelistEnabled)}
              style={{
                width: 48, height: 28, borderRadius: 14,
                background: ipWhitelistEnabled ? "var(--primary)" : "var(--border)",
                border: "none",
                cursor: "pointer",
                position: "relative",
              }}
            >
              <div style={{
                width: 24, height: 24, borderRadius: "50%",
                background: "white",
                position: "absolute",
                top: 2,
                left: ipWhitelistEnabled ? 22 : 2,
              }} />
            </button>
          </div>
          
          {ipWhitelistEnabled && (
            <div>
              <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "var(--muted-foreground)", marginBottom: 6 }}>IPs permitidas (una por línea)</label>
              <textarea 
                value={ipWhitelist} onChange={(e) => setIpWhitelist(e.target.value)}
                placeholder="192.168.1.1&#10;10.0.0.0/24"
                style={{ 
                  width: "100%", height: 100, padding: 12, borderRadius: 8, 
                  border: "1px solid var(--border)", background: "var(--input)",
                  resize: "none", fontFamily: "monospace", fontSize: 13
                }}
              />
            </div>
          )}
        </Card>

        <Card style={{ padding: 24, background: "var(--card)", border: "1px solid var(--border)", borderRadius: "var(--radius)" }}>
          <h2 style={{ fontSize: 16, fontWeight: 700, color: "var(--foreground)", margin: "0 0 20px" }}>
            <Lock size={18} style={{ display: "inline", marginRight: 8 }} />
            Política de Contraseñas
          </h2>
          
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
            <div>
              <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "var(--muted-foreground)", marginBottom: 6 }}>Longitud mínima</label>
              <select 
                value={passwordMinLength} onChange={(e) => setPasswordMinLength(Number(e.target.value))}
                style={{ width: "100%", height: 40, padding: "0 12px", borderRadius: 8, border: "1px solid var(--border)", background: "var(--input)" }}
              >
                <option value="6">6 caracteres</option>
                <option value="8">8 caracteres</option>
                <option value="10">10 caracteres</option>
                <option value="12">12 caracteres</option>
              </select>
            </div>
            <div>
              <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "var(--muted-foreground)", marginBottom: 6 }}>Tiempo de sesión (minutos)</label>
              <select 
                value={sessionTimeout} onChange={(e) => setSessionTimeout(Number(e.target.value))}
                style={{ width: "100%", height: 40, padding: "0 12px", borderRadius: 8, border: "1px solid var(--border)", background: "var(--input)" }}
              >
                <option value="15">15 minutos</option>
                <option value="30">30 minutos</option>
                <option value="60">1 hora</option>
                <option value="120">2 horas</option>
                <option value="480">8 horas</option>
              </select>
            </div>
          </div>

          <div style={{ marginTop: 16, display: "flex", flexDirection: "column", gap: 12 }}>
            <label style={{ display: "flex", alignItems: "center", gap: 12, cursor: "pointer" }}>
              <input 
                type="checkbox" 
                checked={passwordRequireSpecial} 
                onChange={(e) => setPasswordRequireSpecial(e.target.checked)}
                style={{ width: 18, height: 18 }}
              />
              <span style={{ fontSize: 13, color: "var(--foreground)" }}>Requerir carácter especial (@, #, $...)</span>
            </label>
            <label style={{ display: "flex", alignItems: "center", gap: 12, cursor: "pointer" }}>
              <input 
                type="checkbox" 
                checked={passwordRequireNumber} 
                onChange={(e) => setPasswordRequireNumber(e.target.checked)}
                style={{ width: 18, height: 18 }}
              />
              <span style={{ fontSize: 13, color: "var(--foreground)" }}>Requerir al menos un número</span>
            </label>
          </div>
        </Card>

        <Card style={{ padding: 24, background: "var(--card)", border: "1px solid var(--border)", borderRadius: "var(--radius)" }}>
          <h2 style={{ fontSize: 16, fontWeight: 700, color: "var(--foreground)", margin: "0 0 20px" }}>
            <Users size={18} style={{ display: "inline", marginRight: 8 }} />
            Sesiones Activas
          </h2>
          
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {sesionesActivas.map((sesion) => (
              <div key={sesion.id} style={{ 
                display: "flex", justifyContent: "space-between", alignItems: "center",
                padding: 16, background: "var(--secondary)", borderRadius: 12
              }}>
                <div>
                  <p style={{ fontSize: 14, fontWeight: 600, color: "var(--foreground)", margin: "0 0 4px" }}>
                    {sesion.dispositivo}
                    {sesion.actual && <Badge style={{ marginLeft: 8, background: "var(--primary-light)", color: "var(--primary)", border: "none" }}>Actual</Badge>}
                  </p>
                  <p style={{ fontSize: 12, color: "var(--muted-foreground)", margin: 0 }}>
                    {sesion.ubicacion} • {sesion.ultimaActividad}
                  </p>
                </div>
                {!sesion.actual && (
                  <Button size="sm" variant="outline" style={{ color: "var(--destructive)" }}>
                    Cerrar sesión
                  </Button>
                )}
              </div>
            ))}
          </div>
        </Card>

        <Card style={{ padding: 24, background: "var(--card)", border: "1px solid var(--border)", borderRadius: "var(--radius)" }}>
          <h2 style={{ fontSize: 16, fontWeight: 700, color: "var(--foreground)", margin: "0 0 20px" }}>
            <Clock size={18} style={{ display: "inline", marginRight: 8 }} />
            Retención de Datos
          </h2>
          
          <div>
            <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "var(--muted-foreground)", marginBottom: 6 }}>Días de retención de logs y conversaciones</label>
            <select 
              value={retentionDays} onChange={(e) => setRetentionDays(Number(e.target.value))}
              style={{ width: "100%", height: 40, padding: "0 12px", borderRadius: 8, border: "1px solid var(--border)", background: "var(--input)" }}
            >
              <option value="30">30 días</option>
              <option value="60">60 días</option>
              <option value="90">90 días</option>
              <option value="180">180 días</option>
              <option value="365">1 año</option>
            </select>
            <p style={{ fontSize: 11, color: "var(--muted-foreground)", margin: "6px 0 0" }}>
              Los datos más antiguos serán eliminados automáticamente
            </p>
          </div>
        </Card>

        <div style={{ display: "flex", justifyContent: "flex-end" }}>
          <Button onClick={handleSave} disabled={saving} style={{ background: "var(--primary)", color: "white" }}>
            {saving ? "Guardando..." : "Guardar configuración"}
          </Button>
        </div>
      </div>
    </div>
  );
}