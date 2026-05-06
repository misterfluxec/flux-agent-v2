"use client";

import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useLocale, useTranslations } from 'next-intl';
import { Eye, EyeOff, Zap, Shield, Activity, Sun, Moon, Building2, User, Palette, Globe2, CheckCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";
import SocialLoginButtons from "@/components/auth/SocialLoginButtons";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "https://api.labodegaec.com";

function RegisterContent() {
  const router = useRouter();
  const locale = useLocale();
  const t = useTranslations('auth.register');
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
        toast.error(t('error'), {
          description: (err as { detail?: string }).detail ?? t('error_desc'),
        });
        setLoading(false);
        return;
      }

      const data = await resp.json();

      toast.success(t('success'), { description: t('success_desc') });

      localStorage.setItem("flux_token", data.access_token);
      localStorage.setItem("flux_tenant_id", data.usuario.tenant_id);
      localStorage.setItem("flux_user_nombre", data.usuario.nombre);
      localStorage.setItem("flux_user_email", data.usuario.email);
      localStorage.setItem("flux_user_rol", data.usuario.rol);
      localStorage.setItem("flux_user_plan", data.usuario.plan);
      localStorage.setItem("flux_empresa", data.usuario.nombre_empresa || "");

      setTimeout(() => {
        router.push(`/${locale}/dashboard`);
      }, 1500);
    } catch {
      toast.error(t('conn_error'), { description: t('conn_error_desc') });
      setLoading(false);
    }
  }

  if (!mounted) return null;

  const isDark = theme === "dark";

  const planes = [
    { id: "starter", nombre: t('plans.starter.name'), precio: 0, desc: t('plans.starter.desc') },
    { id: "pro", nombre: t('plans.pro.name'), precio: 49, desc: t('plans.pro.desc') },
    { id: "enterprise", nombre: t('plans.enterprise.name'), precio: 199, desc: t('plans.enterprise.desc') },
  ];

  return (
    <div className="min-h-screen bg-background text-foreground flex items-center justify-center p-4 relative overflow-hidden font-sans py-12">
      {/* Background Effects */}
      <div className="absolute inset-0 z-0">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-primary/10 blur-[120px] rounded-full animate-pulse" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-blue-600/10 blur-[120px] rounded-full animate-pulse delay-700" />
        <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 mix-blend-soft-light pointer-events-none" />
        <div className="grid-tactical fixed inset-0 pointer-events-none opacity-[0.03] dark:opacity-[0.07]" />
      </div>

      {/* Floating Theme Toggle */}
      <button
        onClick={toggleTheme}
        className="fixed top-8 right-8 z-50 p-3 bg-card/50 backdrop-blur-md border border-border rounded-2xl shadow-xl hover:scale-110 transition-all active:scale-95 group"
      >
        {theme === 'dark' ? (
          <Sun className="w-5 h-5 text-yellow-500 group-hover:rotate-45 transition-transform" />
        ) : (
          <Moon className="w-5 h-5 text-blue-600 group-hover:-rotate-12 transition-transform" />
        )}
      </button>

      <div className="w-full max-w-lg relative z-10 animate-in fade-in zoom-in-95 duration-700">
        <div className="bg-card/40 backdrop-blur-2xl border border-white/10 dark:border-white/5 rounded-[40px] p-8 md:p-10 shadow-[0_32px_64px_-16px_rgba(0,0,0,0.2)]">
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
              <p className="text-[10px] font-black uppercase tracking-widest text-muted-foreground m-0">
                {isDark ? t('badge_dark') : t('badge_light')}
              </p>
              <h1 className="text-xl md:text-2xl font-black tracking-tight mb-2 bg-gradient-to-br from-purple-400 to-cyan-400 bg-clip-text text-transparent">
                {t('title')}
              </h1>
            </div>
          </div>

          <div style={{
            borderLeft: "2px solid var(--primary)",
            paddingLeft: 14,
          }}>
            <p style={{ fontSize: 13, color: "var(--muted-foreground)", margin: 0 }}>
              {t('subtitle')}
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
            <span style={{ fontSize: 13, fontWeight: 600, color: "var(--foreground)" }}>{t('type_individual')}</span>
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
            <span style={{ fontSize: 13, fontWeight: 600, color: "var(--foreground)" }}>{t('type_company')}</span>
          </button>
        </div>

        {/* Social Login Buttons */}
        <SocialLoginButtons />

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          {tipo === "empresa" && (
            <div>
              <label className="text-[11px] font-black uppercase tracking-[0.06em] text-muted-foreground block mb-[6px]">
                {t('company_name')}
              </label>
              <div style={{ position: "relative" }}>
                <Building2 size={16} style={{ position: "absolute", left: 12, top: "50%", transform: "translateY(-50%)", color: "var(--muted-foreground)" }} />
                <Input
                  type="text" required
                  value={empresa} onChange={e => setEmpresa(e.target.value)}
                  placeholder={t('company_placeholder')}
                  className="h-14 pl-12 bg-background/50 border-border/50 rounded-2xl focus:ring-primary/20 focus:border-primary/50 transition-all font-medium"
                />
              </div>
            </div>
          )}

          <div>
            <label className="text-[11px] font-black uppercase tracking-[0.06em] text-muted-foreground block mb-[6px]">
              {t('name_label')}
            </label>
            <div style={{ position: "relative" }}>
              <User size={16} style={{ position: "absolute", left: 12, top: "50%", transform: "translateY(-50%)", color: "var(--muted-foreground)" }} />
              <Input
                type="text" required
                value={nombre} onChange={e => setNombre(e.target.value)}
                placeholder={t('name_placeholder')}
                className="h-14 pl-12 bg-background/50 border-border/50 rounded-2xl focus:ring-primary/20 focus:border-primary/50 transition-all font-medium"
              />
            </div>
          </div>

          <div>
            <label className="text-[11px] font-black uppercase tracking-[0.06em] text-muted-foreground block mb-[6px]">
              {t('email_label')}
            </label>
            <Input
              type="email" autoComplete="email" required
              value={email} onChange={e => setEmail(e.target.value)}
              placeholder={t('email_placeholder')}
              className="h-14 px-4 bg-background/50 border-border/50 rounded-2xl focus:ring-primary/20 focus:border-primary/50 transition-all font-medium"
            />
          </div>

          <div>
            <label className="text-[11px] font-black uppercase tracking-[0.06em] text-muted-foreground block mb-[6px]">
              {t('password_label')}
            </label>
            <div style={{ position: "relative" }}>
              <Input
                type={showPwd ? "text" : "password"}
                required minLength={6}
                value={password} onChange={e => setPassword(e.target.value)}
                placeholder={t('password_placeholder')}
                className="h-14 pl-4 pr-12 bg-background/50 border-border/50 rounded-2xl focus:ring-primary/20 focus:border-primary/50 transition-all font-medium"
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
            <label className="text-[11px] font-black uppercase tracking-[0.06em] text-muted-foreground block mb-2">
              {t('plan_label')}
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
                    {p.precio === 0 ? t('free') : `$${p.precio}${t('per_month')}`}
                  </p>
                </button>
              ))}
            </div>
          </div>

          {tipo === "empresa" && (
            <div>
              <label className="text-[11px] font-black uppercase tracking-[0.06em] text-muted-foreground block mb-2">
                <Palette size={12} style={{ display: "inline", marginRight: 4 }} />
                {t('brand_color')}
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
                {t('portal_includes')}
              </p>
              <ul style={{ fontSize: 11, color: "var(--muted-foreground)", margin: 0, paddingLeft: 16 }}>
                {t.raw('portal_features').map((f: string, i: number) => (
                  <li key={i}>{f}</li>
                ))}
              </ul>
            </div>
          )}

          <Button
            type="submit" disabled={loading}
            className="w-full h-14 bg-primary hover:bg-primary/90 text-primary-foreground rounded-2xl font-black text-sm uppercase tracking-widest shadow-xl shadow-primary/20 group transition-all active:scale-[0.98] mt-6"
          >
            {loading
              ? <span style={{ display: "flex", alignItems: "center", gap: 8, justifyContent: "center" }}>
                  <span style={{ width: 16, height: 16, border: "2px solid currentColor", borderTopColor: "transparent", borderRadius: "50%", display: "inline-block", animation: "spin 0.7s linear infinite" }} />
                  {t('creating_env')}
                </span>
              : tipo === "empresa" ? t('submit_company') : t('submit_individual')
            }
          </Button>
        </form>

        <div style={{ marginTop: 20, textAlign: "center" }}>
          <p style={{ fontSize: 13, color: "var(--muted-foreground)" }}>
            {t('already_have_account')}{" "}
            <button onClick={() => router.push(`/${locale}/login`)} style={{ color: "var(--primary)", fontWeight: 600, background: "none", border: "none", cursor: "pointer", textDecoration: "underline" }}>
              {t('login')}
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
            <span>{isDark ? t('jwt_encryption') : t('secure_data')}</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <span className="pulse-live" style={{ width: 6, height: 6, borderRadius: "50%", background: "var(--success)", display: "inline-block" }} />
            <Activity size={11} />
            <span>{isDark ? t('rls_isolation') : t('multi_tenant')}</span>
          </div>
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