"use client";

import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Eye, EyeOff, Zap, Shield, Activity, Sun, Moon, Building2, User, Palette, Globe2, CheckCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";
import SocialLoginButtons from "@/components/auth/SocialLoginButtons";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "https://api.labodegaec.com";

function RegisterContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  
  const tipoParam = searchParams.get("tipo") || "individual";
  const isEmpresa = tipoParam === "empresa";
  
  const [tipo, setTipo] = useState<"individual" | "empresa">(isEmpresa ? "empresa" : "individual");
  const [empresa, setEmpresa] = useState("");
  const [nombre, setNombre] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [plan, setPlan] = useState("starter");
  const [colorPrimario, setColorPrimario] = useState("#6366f1");
  const [showPwd, setShowPwd] = useState(false);
  const [loading, setLoading] = useState(false);
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem("flux_theme") as "light" | "dark" | null;
    const system = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    const initial = stored ?? system;
    setTheme(initial);
    document.documentElement.classList.toggle("dark", initial === "dark");
    setMounted(true);
  }, []);

  useEffect(() => {
    const t = searchParams.get("tipo");
    if (t === "empresa") setTipo("empresa");
    else if (t === "individual") setTipo("individual");
  }, [searchParams]);

  const toggleTheme = () => {
    setTheme(prev => {
      const next = prev === "light" ? "dark" : "light";
      localStorage.setItem("flux_theme", next);
      document.documentElement.classList.toggle("dark", next === "dark");
      return next;
    });
  };

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);

    const payload: any = {
      nombre_usuario: nombre.trim(),
      email: email.trim().toLowerCase(),
      password,
      plan,
    };

    if (tipo === "empresa") {
      payload.nombre_empresa = empresa.trim();
      payload.branding = {
        color_primario: colorPrimario,
      };
    } else {
      payload.nombre_empresa = empresa.trim() || `${nombre.trim()} Store`;
    }

    try {
      const resp = await fetch(`${BACKEND_URL}/api/v1/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        toast.error("Error al registrarse", {
          description: (err as { detail?: string }).detail ?? "Revisa los datos e intenta de nuevo.",
        });
        setLoading(false);
        return;
      }

      const data = await resp.json();

      toast.success("¡Registro Exitoso!", { description: "Preparando tu espacio de trabajo..." });

      localStorage.setItem("flux_token", data.access_token);
      localStorage.setItem("flux_tenant_id", data.usuario.tenant_id);
      localStorage.setItem("flux_user_nombre", data.usuario.nombre);
      localStorage.setItem("flux_user_email", data.usuario.email);
      localStorage.setItem("flux_user_rol", data.usuario.rol);
      localStorage.setItem("flux_user_plan", data.usuario.plan);
      localStorage.setItem("flux_empresa", data.usuario.nombre_empresa || "");

      setTimeout(() => {
        router.push("/dashboard");
      }, 1500);
    } catch {
      toast.error("Error de conexión", { description: "No se pudo conectar con el servidor." });
      setLoading(false);
    }
  }

  if (!mounted) return null;

  const isDark = theme === "dark";

  const planes = [
    { id: "starter", nombre: "Starter", precio: 0, desc: "Para comenzar" },
    { id: "pro", nombre: "Pro", precio: 49, desc: "Más funcionalidades" },
    { id: "enterprise", nombre: "Enterprise", precio: 199, desc: "Marca blanca" },
  ];

  return (
    <div className="min-h-dvh flex items-center justify-center p-4 relative" style={{ background: "var(--background)" }}>
      <div className="grid-tactical fixed inset-0 pointer-events-none" style={{ opacity: isDark ? 0.45 : 0.6 }} />
      <div className="fixed left-0 top-0 bottom-0 w-1" style={{ background: "var(--primary)" }} />

      <button
        onClick={toggleTheme}
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
        {isDark ? <><Sun size={13} /> <span>Modo Claro</span></> : <><Moon size={13} /> <span>Modo Oscuro</span></>}
      </button>

      <div className="w-full max-w-lg animate-entry relative z-10" style={{
        background: "var(--card)",
        border: "1px solid var(--border)",
        borderRadius: isDark ? "0px" : "16px",
        padding: "32px 28px",
        boxShadow: isDark ? "0 0 0 1px var(--border), 0 20px 60px rgb(0 0 0 / 0.5)" : "var(--shadow-lg)",
      }}>
        <div style={{ marginBottom: 28 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 20 }}>
            <div style={{
              width: 42, height: 42,
              background: "var(--primary)",
              color: "var(--primary-foreground)",
              display: "flex", alignItems: "center", justifyContent: "center",
              borderRadius: isDark ? "0px" : "12px",
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
              }}>
                {isDark ? "CREAR CUENTA" : "Onboarding"}
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
              {isDark ? "Configura tu Agente Inteligente" : "Automatiza tus ventas hoy"}
            </p>
          </div>
        </div>

        <div style={{ display: "flex", gap: 8, marginBottom: 24 }}>
          <button
            type="button"
            onClick={() => setTipo("individual")}
            style={{
              flex: 1,
              padding: "12px 16px",
              borderRadius: isDark ? "0px" : "12px",
              border: `2px solid ${tipo === "individual" ? "var(--primary)" : "var(--border)"}`,
              background: tipo === "individual" ? "var(--primary-light)" : "transparent",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: 8,
            }}
          >
            <User size={18} style={{ color: tipo === "individual" ? "var(--primary)" : "var(--muted-foreground)" }} />
            <span style={{ fontSize: 13, fontWeight: 600, color: "var(--foreground)" }}>Individual</span>
          </button>
          <button
            type="button"
            onClick={() => setTipo("empresa")}
            style={{
              flex: 1,
              padding: "12px 16px",
              borderRadius: isDark ? "0px" : "12px",
              border: `2px solid ${tipo === "empresa" ? "var(--primary)" : "var(--border)"}`,
              background: tipo === "empresa" ? "var(--primary-light)" : "transparent",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: 8,
            }}
          >
            <Building2 size={18} style={{ color: tipo === "empresa" ? "var(--primary)" : "var(--muted-foreground)" }} />
            <span style={{ fontSize: 13, fontWeight: 600, color: "var(--foreground)" }}>Empresa</span>
          </button>
        </div>

        {/* Social Login Buttons */}
        <SocialLoginButtons />

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          {tipo === "empresa" && (
            <div>
              <label style={{
                display: "block", marginBottom: 6,
                fontSize: 11, fontWeight: 600,
                color: "var(--muted-foreground)",
                textTransform: "uppercase",
                letterSpacing: "0.06em",
              }}>
                Nombre de tu Empresa *
              </label>
              <div style={{ position: "relative" }}>
                <Building2 size={16} style={{ position: "absolute", left: 12, top: "50%", transform: "translateY(-50%)", color: "var(--muted-foreground)" }} />
                <Input
                  type="text" required
                  value={empresa} onChange={e => setEmpresa(e.target.value)}
                  placeholder="Acme Corp"
                  style={{
                    height: 44, fontSize: 14, paddingLeft: 38,
                    background: "var(--input)",
                    border: "1px solid var(--border)",
                    color: "var(--foreground)",
                    borderRadius: isDark ? "0px" : "10px",
                  }}
                />
              </div>
            </div>
          )}

          <div>
            <label style={{
              display: "block", marginBottom: 6,
              fontSize: 11, fontWeight: 600,
              color: "var(--muted-foreground)",
              textTransform: "uppercase",
              letterSpacing: "0.06em",
            }}>
              Tu Nombre
            </label>
            <div style={{ position: "relative" }}>
              <User size={16} style={{ position: "absolute", left: 12, top: "50%", transform: "translateY(-50%)", color: "var(--muted-foreground)" }} />
              <Input
                type="text" required
                value={nombre} onChange={e => setNombre(e.target.value)}
                placeholder="Juan Pérez"
                style={{
                  height: 44, fontSize: 14, paddingLeft: 38,
                  background: "var(--input)",
                  border: "1px solid var(--border)",
                  color: "var(--foreground)",
                  borderRadius: isDark ? "0px" : "10px",
                }}
              />
            </div>
          </div>

          <div>
            <label style={{
              display: "block", marginBottom: 6,
              fontSize: 11, fontWeight: 600,
              color: "var(--muted-foreground)",
              textTransform: "uppercase",
              letterSpacing: "0.06em",
            }}>
              Correo electrónico
            </label>
            <Input
              type="email" autoComplete="email" required
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

          <div>
            <label style={{
              display: "block", marginBottom: 6,
              fontSize: 11, fontWeight: 600,
              color: "var(--muted-foreground)",
              textTransform: "uppercase",
              letterSpacing: "0.06em",
            }}>
              Contraseña
            </label>
            <div style={{ position: "relative" }}>
              <Input
                type={showPwd ? "text" : "password"}
                required minLength={6}
                value={password} onChange={e => setPassword(e.target.value)}
                placeholder="Mínimo 6 caracteres"
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

          <div>
            <label style={{
              display: "block", marginBottom: 8,
              fontSize: 11, fontWeight: 600,
              color: "var(--muted-foreground)",
              textTransform: "uppercase",
              letterSpacing: "0.06em",
            }}>
              Plan
            </label>
            <div style={{ display: "flex", gap: 8 }}>
              {planes.map(p => (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => setPlan(p.id)}
                  style={{
                    flex: 1,
                    padding: "10px 8px",
                    borderRadius: isDark ? "0px" : "10px",
                    border: `2px solid ${plan === p.id ? "var(--primary)" : "var(--border)"}`,
                    background: plan === p.id ? "var(--primary-light)" : "transparent",
                    cursor: "pointer",
                    textAlign: "center",
                  }}
                >
                  <p style={{ fontSize: 12, fontWeight: 700, color: "var(--foreground)", margin: 0 }}>{p.nombre}</p>
                  <p style={{ fontSize: 10, color: "var(--muted-foreground)", margin: "2px 0 0" }}>
                    {p.precio === 0 ? "Gratis" : `$${p.precio}/mes`}
                  </p>
                </button>
              ))}
            </div>
          </div>

          {tipo === "empresa" && (
            <div>
              <label style={{
                display: "block", marginBottom: 8,
                fontSize: 11, fontWeight: 600,
                color: "var(--muted-foreground)",
                textTransform: "uppercase",
                letterSpacing: "0.06em",
              }}>
                <Palette size={12} style={{ display: "inline", marginRight: 4 }} />
                Color de marca
              </label>
              <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                <input
                  type="color"
                  value={colorPrimario}
                  onChange={e => setColorPrimario(e.target.value)}
                  style={{ width: 40, height: 40, border: "1px solid var(--border)", borderRadius: 8, cursor: "pointer" }}
                />
                <div style={{ flex: 1, display: "flex", gap: 6 }}>
                  {["#6366f1", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4"].map(c => (
                    <button
                      key={c}
                      type="button"
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
          )}

          {tipo === "empresa" && (
            <div style={{
              padding: 12,
              background: "var(--primary-light)",
              borderRadius: isDark ? "0px" : "10px",
              border: "1px solid var(--primary-mid)",
            }}>
              <p style={{ fontSize: 12, fontWeight: 600, color: "var(--primary)", margin: "0 0 6px", display: "flex", alignItems: "center", gap: 6 }}>
                <CheckCircle size={14} />
                Incluye Portal Corporativo
              </p>
              <ul style={{ fontSize: 11, color: "var(--muted-foreground)", margin: 0, paddingLeft: 16 }}>
                <li>Marca blanca completa</li>
                <li>Logo y colores personalizados</li>
                <li>Múltiples agentes IA</li>
                <li>Soporte prioritario</li>
              </ul>
            </div>
          )}

          <Button
            type="submit" disabled={loading}
            style={{
              height: 46, marginTop: 8,
              background: "var(--primary)",
              color: "var(--primary-foreground)",
              fontWeight: 700,
              fontSize: 13,
              borderRadius: isDark ? "0px" : "10px",
              border: "none",
              cursor: loading ? "not-allowed" : "pointer",
              opacity: loading ? 0.7 : 1,
              boxShadow: isDark ? `0 0 16px var(--primary)40` : "var(--shadow-sm)",
            }}
          >
            {loading
              ? <span style={{ display: "flex", alignItems: "center", gap: 8, justifyContent: "center" }}>
                  <span style={{ width: 16, height: 16, border: "2px solid currentColor", borderTopColor: "transparent", borderRadius: "50%", display: "inline-block", animation: "spin 0.7s linear infinite" }} />
                  Creando entorno...
                </span>
              : tipo === "empresa" ? "Crear Portal Corporativo" : "Crear mi cuenta"
            }
          </Button>
        </form>

        <div style={{ marginTop: 20, textAlign: "center" }}>
          <p style={{ fontSize: 13, color: "var(--muted-foreground)" }}>
            ¿Ya tienes una cuenta?{" "}
            <button onClick={() => router.push("/login")} style={{ color: "var(--primary)", fontWeight: 600, background: "none", border: "none", cursor: "pointer", textDecoration: "underline" }}>
              Iniciar sesión
            </button>
          </p>
        </div>

        <div style={{
          marginTop: 20,
          padding: "10px 14px",
          display: "flex", alignItems: "center", justifyContent: "space-between",
          fontSize: 11,
          color: "var(--muted-foreground)",
          border: "1px solid var(--border)",
          borderRadius: isDark ? "0px" : "10px",
          background: "var(--secondary)",
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <Shield size={12} />
            <span>{isDark ? "ENCRIPTACIÓN JWT" : "Datos seguros"}</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <span className="pulse-live" style={{ width: 6, height: 6, borderRadius: "50%", background: "var(--success)", display: "inline-block" }} />
            <Activity size={11} />
            <span>{isDark ? "AISLAMIENTO RLS" : "Multi-tenant"}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function RegisterPage() {
  return (
    <Suspense fallback={<div>Cargando...</div>}>
      <RegisterContent />
    </Suspense>
  );
}