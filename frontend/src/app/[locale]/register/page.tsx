"use client";

import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useLocale, useTranslations } from 'next-intl';
import { Eye, EyeOff, Zap, Shield, Activity, Sun, Moon, Building2, User, Palette, Globe2, CheckCircle, Mail, Lock } from "lucide-react";
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

      <div className="w-full max-w-md relative z-10 animate-in fade-in zoom-in-95 duration-700">
        <div className="bg-card/40 backdrop-blur-2xl border border-white/10 dark:border-white/5 rounded-[40px] p-10 md:p-12 shadow-[0_32px_64px_-16px_rgba(0,0,0,0.2)]">
          
          {/* Header & Branding */}
          <div className="text-center mb-10">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-[22px] bg-gradient-to-br from-primary to-blue-700 shadow-lg shadow-primary/30 mb-6 group transition-transform hover:scale-105 duration-500">
              <Zap className="w-8 h-8 text-white fill-white/20 group-hover:animate-pulse" />
            </div>
            <h1 className="text-3xl font-black tracking-tight mb-2 bg-gradient-to-br from-purple-400 to-cyan-400 bg-clip-text text-transparent">
              {t('title')}
            </h1>
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-primary/10 rounded-full border border-primary/20">
               <span className="w-1.5 h-1.5 bg-primary rounded-full animate-pulse" />
               <p className="text-[10px] font-black uppercase tracking-widest text-primary">
                 {isDark ? t('badge_dark') : t('badge_light')}
               </p>
            </div>
            <p className="text-sm text-muted-foreground mt-3">
              {t('subtitle')}
            </p>
          </div>

          {/* Type Selector */}
          <div className="flex gap-2 mb-6">
            <button
              type="button"
              onClick={() => setTipo("individual")}
              className={`flex-1 flex items-center justify-center gap-2 p-3 rounded-2xl border-2 transition-all font-medium text-sm ${
                tipo === "individual"
                  ? "border-primary bg-primary/10 text-primary"
                  : "border-border/50 bg-background/50 text-foreground hover:bg-background/80"
              }`}
            >
              <User className="w-4 h-4" />
              <span>{t('type_individual')}</span>
            </button>
            <button
              type="button"
              onClick={() => setTipo("empresa")}
              className={`flex-1 flex items-center justify-center gap-2 p-3 rounded-2xl border-2 transition-all font-medium text-sm ${
                tipo === "empresa"
                  ? "border-primary bg-primary/10 text-primary"
                  : "border-border/50 bg-background/50 text-foreground hover:bg-background/80"
              }`}
            >
              <Building2 className="w-4 h-4" />
              <span>{t('type_company')}</span>
            </button>
          </div>

        {/* Social Login Buttons */}
        <SocialLoginButtons />

          <form onSubmit={handleSubmit} className="space-y-5">
          {tipo === "empresa" && (
            <div className="space-y-2">
              <label className="text-[11px] font-black uppercase tracking-[0.2em] text-muted-foreground/70 ml-1">
                {t('company_name')}
              </label>
              <div className="relative group">
                <Building2 className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground group-focus-within:text-primary transition-colors" />
                <Input
                  type="text" required
                  value={empresa} onChange={e => setEmpresa(e.target.value)}
                  placeholder={t('company_placeholder')}
                  className="h-14 pl-12 bg-background/50 border-border/50 rounded-2xl focus:ring-primary/20 focus:border-primary/50 transition-all font-medium"
                />
              </div>
            </div>
          )}

            <div className="space-y-2">
              <label className="text-[11px] font-black uppercase tracking-[0.2em] text-muted-foreground/70 ml-1">
                {t('name_label')}
              </label>
              <div className="relative group">
                <User className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground group-focus-within:text-primary transition-colors" />
                <Input
                  type="text" required
                  value={nombre} onChange={e => setNombre(e.target.value)}
                  placeholder={t('name_placeholder')}
                  className="h-14 pl-12 bg-background/50 border-border/50 rounded-2xl focus:ring-primary/20 focus:border-primary/50 transition-all font-medium"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-[11px] font-black uppercase tracking-[0.2em] text-muted-foreground/70 ml-1">
                {t('email_label')}
              </label>
              <div className="relative group">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground group-focus-within:text-primary transition-colors" />
                <Input
                  type="email" autoComplete="email" required
                  value={email} onChange={e => setEmail(e.target.value)}
                  placeholder={t('email_placeholder')}
                  className="h-14 pl-12 bg-background/50 border-border/50 rounded-2xl focus:ring-primary/20 focus:border-primary/50 transition-all font-medium"
                />
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between items-center px-1">
                <label className="text-[11px] font-black uppercase tracking-[0.2em] text-muted-foreground/70">
                  {t('password_label')}
                </label>
                <span className="text-[10px] text-muted-foreground">
                  {t('password_min')}
                </span>
              </div>
              <div className="relative group">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground group-focus-within:text-primary transition-colors" />
                <Input
                  type={showPwd ? "text" : "password"}
                  required minLength={6}
                  value={password} onChange={e => setPassword(e.target.value)}
                  placeholder={t('password_placeholder')}
                  className="h-14 pl-12 pr-12 bg-background/50 border-border/50 rounded-2xl focus:ring-primary/20 focus:border-primary/50 transition-all font-medium"
                />
                <button
                  type="button"
                  onClick={() => setShowPwd(v => !v)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 p-1 text-muted-foreground hover:text-foreground transition-colors"
                >
                  {showPwd ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-[11px] font-black uppercase tracking-[0.2em] text-muted-foreground/70 ml-1">
                {t('plan_label')}
              </label>
              <div className="flex gap-2">
                {planes.map(p => (
                  <button
                    key={p.id}
                    type="button"
                    onClick={() => setPlan(p.id)}
                    className={`flex-1 p-2 rounded-xl border-2 transition-all text-center ${
                      plan === p.id
                        ? "border-primary bg-primary/10 text-primary"
                        : "border-border/50 bg-background/50 text-foreground hover:bg-background/80"
                    }`}
                  >
                    <p className="text-xs font-bold text-foreground">{p.nombre}</p>
                    <p className="text-[9px] text-muted-foreground mt-0.5">
                      {p.precio === 0 ? t('free') : `$${p.precio}${t('per_month')}`}
                    </p>
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-[11px] font-black uppercase tracking-[0.2em] text-muted-foreground/70 ml-1">
                <Palette className="w-3 h-3 inline mr-1" />
                {t('brand_color')}
              </label>
              <div className="flex gap-2 items-center">
                <input
                  type="color"
                  value={colorPrimario}
                  onChange={e => setColorPrimario(e.target.value)}
                  className="w-10 h-10 border border-border rounded-lg cursor-pointer"
                />
                <div className="flex gap-1.5">
                  {["#6366f1", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4"].map(c => (
                    <button
                      key={c}
                      type="button"
                      onClick={() => setColorPrimario(c)}
                      className={`w-7 h-7 rounded-md border-2 transition-all ${
                        colorPrimario === c
                          ? "border-foreground"
                          : "border-border hover:border-primary/50"
                      }`}
                      style={{ backgroundColor: c }}
                    />
                  ))}
                </div>
              </div>
            </div>

          {tipo === "empresa" && (
            <div className="p-3 bg-primary/10 rounded-xl border border-primary/20">
              <p className="text-xs font-semibold text-primary flex items-center gap-1.5 mb-1.5">
                <CheckCircle className="w-3.5 h-3.5" />
                {t('portal_includes')}
              </p>
              <ul className="text-[10px] text-muted-foreground space-y-0.5">
                {t.raw('portal_features').map((f: string, i: number) => (
                  <li key={i} className="list-disc list-inside">{f}</li>
                ))}
              </ul>
            </div>
          )}

            <Button
              type="submit" disabled={loading}
              className="w-full h-14 bg-primary hover:bg-primary/90 text-primary-foreground rounded-2xl font-black text-sm uppercase tracking-widest shadow-xl shadow-primary/20 group transition-all active:scale-[0.98] mt-6"
            >
              {loading ? (
                <div className="flex items-center gap-3 justify-center">
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>{t('creating_env')}</span>
                </div>
              ) : (
                <span>{tipo === "empresa" ? t('submit_company') : t('submit_individual')}</span>
              )}
            </Button>
          </form>

          {/* Footer Info */}
          <div className="mt-8 pt-6 border-t border-border/50">
            <p className="text-center text-sm text-muted-foreground">
              {t('already_have_account')}{" "}
              <button 
                onClick={() => router.push(`/${locale}/login`)}
                className="text-primary font-semibold hover:underline bg-transparent border-none cursor-pointer"
              >
                {t('login')}
              </button>
            </p>
            
            <div className="flex items-center justify-between px-3 py-2 mt-4 bg-muted/50 rounded-xl border border-border/50 text-xs text-muted-foreground">
              <div className="flex items-center gap-1.5">
                <Shield className="w-3 h-3 text-primary" />
                <span className="font-semibold uppercase tracking-wider">
                  {isDark ? t('jwt_encryption') : t('secure_data')}
                </span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse" />
                <Activity className="w-3 h-3 text-green-500" />
                <span className="font-semibold uppercase tracking-wider">
                  {isDark ? t('rls_isolation') : t('multi_tenant')}
                </span>
              </div>
            </div>
          </div>
        </div>
        
        {/* Version & Credits */}
        <p className="text-center mt-6 text-[10px] font-bold text-muted-foreground/40 uppercase tracking-[0.3em]">
          {t('footer_version')}
        </p>
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