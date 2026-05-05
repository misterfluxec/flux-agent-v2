"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Eye, EyeOff, Zap, Shield, Activity, Sun, Moon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";
import SocialLoginButtons from "@/components/auth/SocialLoginButtons";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "https://api.labodegaec.com";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail]             = useState("");
  const [password, setPassword]       = useState("");
  const [showPwd, setShowPwd]         = useState(false);
  const [loading, setLoading]         = useState(false);
  const [theme, setTheme]             = useState<"light" | "dark">("light");
  const [mounted, setMounted]         = useState(false);

  // ── Apply saved theme on mount ──────────────────────────────────────────
  useEffect(() => {
    const stored  = localStorage.getItem("flux_theme") as "light" | "dark" | null;
    const system  = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    const initial = stored ?? system;
    setTheme(initial);
    document.documentElement.classList.toggle("dark", initial === "dark");
    setMounted(true);
  }, []);

  // ── Toggle theme ────────────────────────────────────────────────────────
  const toggleTheme = () => {
    setTheme(prev => {
      const next = prev === "light" ? "dark" : "light";
      localStorage.setItem("flux_theme", next);
      document.documentElement.classList.toggle("dark", next === "dark");
      return next;
    });
  };

  // ── Auth (Backend Real JWT) ────────────────────────────────────────────────
  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);

    try {
      const resp = await fetch(`${BACKEND_URL}/api/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim().toLowerCase(), password }),
      });

      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        toast.error("Credenciales inválidas", {
          description: (err as { detail?: string }).detail ?? "Revisa tu email y contraseña.",
        });
        setLoading(false);
        return;
      }

      const data = await resp.json() as {
        access_token: string;
        usuario: { tenant_id: string; nombre: string; email: string; rol: string; plan: string; nombre_empresa?: string };
      };

      // Guardar token y datos del usuario
      localStorage.setItem("flux_token",       data.access_token);
      localStorage.setItem("flux_tenant_id",   data.usuario.tenant_id);
      localStorage.setItem("flux_user_nombre",  data.usuario.nombre);
      localStorage.setItem("flux_user_email",   data.usuario.email);
      localStorage.setItem("flux_user_rol",     data.usuario.rol);
      localStorage.setItem("flux_user_plan",    data.usuario.plan);
      localStorage.setItem("flux_empresa",      data.usuario.nombre_empresa ?? "");

      router.push("/dashboard");
    } catch {
      toast.error("Error de conexión", { description: "No se pudo conectar con el servidor." });
      setLoading(false);
    }
  }

  if (!mounted) return null;

  const isDark = theme === "dark";

  return (
    <div
      className="min-h-dvh flex items-center justify-center p-4 relative"
      style={{ background: "var(--background)" }}
    >
      {/* Grid bg — visible en ambos modos via CSS variable --border */}
      <div className="grid-tactical fixed inset-0 pointer-events-none" style={{ opacity: isDark ? 0.45 : 0.6 }} />

      {/* Accent bar izquierda — cyan en dark, negro en light */}
      <div className="fixed left-0 top-0 bottom-0 w-1" style={{ background: "var(--primary)" }} />

      {/* ── Theme toggle (top right) ── */}
      <button
        onClick={toggleTheme}
        title={isDark ? "Cambiar a modo claro" : "Cambiar a modo oscuro"}
        className="fixed top-5 right-5 z-50 flex items-center gap-2 transition-all duration-200"
        style={{
          padding: "7px 14px",
          border: "1px solid var(--border)",
          background: "var(--card)",
          color: "var(--muted-foreground)",
          borderRadius: isDark ? "0px" : "8px",
          fontSize: 12, fontWeight: 500,
          cursor: "pointer",
          boxShadow: "var(--shadow-sm)",
        }}
      >
        {isDark
          ? <><Sun size={13} /> <span>Modo Claro</span></>
          : <><Moon size={13} /> <span>Modo Oscuro</span></>
        }
      </button>

      {/* ── Card principal ── */}
      <div
        className="w-full max-w-sm animate-entry relative z-10"
        style={{
          background: "var(--card)",
          border: "1px solid var(--border)",
          borderRadius: isDark ? "0px" : "16px",
          padding: "40px 36px",
          boxShadow: isDark
            ? "0 0 0 1px var(--border), 0 20px 60px rgb(0 0 0 / 0.5)"
            : "var(--shadow-lg)",
        }}
      >
        {/* Logo */}
        <div style={{ marginBottom: 32 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 20 }}>
            <div style={{
              width: 42, height: 42,
              background: "var(--primary)",
              color: "var(--primary-foreground)",
              display: "flex", alignItems: "center", justifyContent: "center",
              borderRadius: isDark ? "0px" : "12px",
              flexShrink: 0,
              boxShadow: isDark ? `0 0 12px var(--primary)60` : "var(--shadow-sm)",
            }}>
              <Zap size={20} strokeWidth={2.5} />
            </div>
            <div>
              <p style={{
                fontSize: 10, fontWeight: 600,
                color: "var(--muted-foreground)",
                textTransform: "uppercase",
                letterSpacing: isDark ? "0.2em" : "0.08em",
                margin: 0,
                fontFamily: isDark ? "monospace" : "inherit",
              }}>
                {isDark ? "SISTEMA" : "Panel de Control"}
              </p>
              <h1 style={{ fontSize: 18, fontWeight: 800, color: "var(--foreground)", margin: 0 }}>
                FluxAgent V2
              </h1>
            </div>
          </div>

          <div style={{
            borderLeft: "2px solid var(--primary)",
            paddingLeft: 14,
          }}>
            <p style={{ fontSize: 13, color: "var(--muted-foreground)", margin: 0 }}>
              {isDark ? "Panel de Control de Agentes IA" : "Bienvenido de vuelta"}
            </p>
          </div>
        </div>

        {/* Social Login Buttons */}
        <SocialLoginButtons />

        {/* Form */}
        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 18 }}>
          {/* Email */}
          <div>
            <label htmlFor="email" style={{
              display: "block", marginBottom: 6,
              fontSize: 11, fontWeight: 600,
              color: "var(--muted-foreground)",
              textTransform: "uppercase",
              letterSpacing: isDark ? "0.15em" : "0.06em",
              fontFamily: isDark ? "monospace" : "inherit",
            }}>
              {isDark ? "Identificador" : "Correo electrónico"}
            </label>
            <Input
              id="email" type="email" autoComplete="email" required
              value={email} onChange={e => setEmail(e.target.value)}
              placeholder="usuario@empresa.com"
              style={{
                height: 44, fontSize: 14,
                background: "var(--input)",
                border: "1px solid var(--border)",
                color: "var(--foreground)",
                borderRadius: isDark ? "0px" : "10px",
                paddingInline: 14,
              }}
            />
          </div>

          {/* Password */}
          <div>
            <label htmlFor="password" style={{
              display: "block", marginBottom: 6,
              fontSize: 11, fontWeight: 600,
              color: "var(--muted-foreground)",
              textTransform: "uppercase",
              letterSpacing: isDark ? "0.15em" : "0.06em",
              fontFamily: isDark ? "monospace" : "inherit",
            }}>
              {isDark ? "Clave de Acceso" : "Contraseña"}
            </label>
            <div style={{ position: "relative" }}>
              <Input
                id="password"
                type={showPwd ? "text" : "password"}
                autoComplete="current-password" required
                value={password} onChange={e => setPassword(e.target.value)}
                placeholder="••••••••••"
                style={{
                  height: 44, fontSize: 14, paddingRight: 44,
                  background: "var(--input)",
                  border: "1px solid var(--border)",
                  color: "var(--foreground)",
                  borderRadius: isDark ? "0px" : "10px",
                  paddingInline: 14,
                }}
              />
              <button
                type="button"
                onClick={() => setShowPwd(v => !v)}
                aria-label={showPwd ? "Ocultar" : "Mostrar"}
                style={{
                  position: "absolute", right: 12, top: "50%", transform: "translateY(-50%)",
                  background: "transparent", border: "none", cursor: "pointer",
                  color: "var(--muted-foreground)", padding: 4,
                }}
              >
                {showPwd ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          {/* Submit */}
          <Button
            type="submit" disabled={loading}
            style={{
              height: 46, marginTop: 4,
              background: "var(--primary)",
              color: "var(--primary-foreground)",
              fontWeight: 700,
              fontSize: 13,
              letterSpacing: isDark ? "0.12em" : "0.03em",
              borderRadius: isDark ? "0px" : "10px",
              border: "none",
              cursor: loading ? "not-allowed" : "pointer",
              opacity: loading ? 0.7 : 1,
              transition: "all 0.2s",
              boxShadow: isDark ? `0 0 16px var(--primary)40` : "var(--shadow-sm)",
            }}
          >
            {loading
              ? <span style={{ display: "flex", alignItems: "center", gap: 8, justifyContent: "center" }}>
                  <span style={{ width: 16, height: 16, border: "2px solid currentColor", borderTopColor: "transparent", borderRadius: "50%", display: "inline-block", animation: "spin 0.7s linear infinite" }} />
                  Autenticando...
                </span>
              : isDark ? "ACCEDER AL SISTEMA" : "Iniciar Sesión"
            }
          </Button>
        </form>

        <div style={{ marginTop: 24, textAlign: "center" }}>
          <p style={{ fontSize: 13, color: "var(--muted-foreground)" }}>
            ¿No tienes cuenta?{" "}
            <button 
              onClick={() => router.push("/register")}
              style={{ color: "var(--primary)", fontWeight: 600, background: "none", border: "none", cursor: "pointer", textDecoration: "underline" }}
            >
              Regístrate gratis
            </button>
          </p>
        </div>

        {/* Status strip */}
        <div style={{
          marginTop: 28,
          padding: "10px 14px",
          display: "flex", alignItems: "center", justifyContent: "space-between",
          fontSize: 11,
          fontFamily: isDark ? "monospace" : "inherit",
          color: "var(--muted-foreground)",
          border: "1px solid var(--border)",
          borderRadius: isDark ? "0px" : "10px",
          background: "var(--secondary)",
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <Shield size={12} />
            <span>{isDark ? "ACCESO SEGURO" : "Conexión segura"}</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <span className="pulse-live" style={{
              width: 6, height: 6, borderRadius: "50%",
              background: "var(--success)", display: "inline-block",
            }} />
            <Activity size={11} />
            <span>{isDark ? "SISTEMA EN LÍNEA" : "En línea"}</span>
          </div>
        </div>

        {/* Demo credentials hint */}
        <p style={{ marginTop: 16, textAlign: "center", fontSize: 11, color: "var(--muted-foreground)" }}>
          Demo:{" "}
          <span style={{ color: "var(--primary)", fontWeight: 600, fontFamily: "monospace" }}>
            admin@fluxagent.io
          </span>
          {" / "}
          <span style={{ color: "var(--primary)", fontWeight: 600, fontFamily: "monospace" }}>
            flux2025
          </span>
        </p>
      </div>

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to   { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
