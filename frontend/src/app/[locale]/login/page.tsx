"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useLocale } from 'next-intl';
import { Eye, EyeOff, Zap, Shield, Activity, Sun, Moon, ArrowRight, Lock, Mail } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";
import SocialLoginButtons from "@/components/auth/SocialLoginButtons";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "https://api.labodegaec.com";

export default function LoginPage() {
  const router = useRouter();
  const locale = useLocale();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
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

    try {
      const resp = await fetch(`${BACKEND_URL}/api/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim().toLowerCase(), password }),
      });

      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        toast.error("Acceso Denegado", {
          description: (err as { detail?: string }).detail ?? "Verifica tus credenciales e intenta de nuevo.",
        });
        setLoading(false);
        return;
      }

      const data = await resp.json() as any;
      localStorage.setItem("flux_token", data.access_token);
      localStorage.setItem("flux_tenant_id", data.usuario.tenant_id);
      router.push("/dashboard");
    } catch {
      toast.error("Error Crítico", { description: "No se pudo establecer conexión con el núcleo." });
      setLoading(false);
    }
  }

  if (!mounted) return null;

  return (
    <div className="min-h-screen bg-background text-foreground flex items-center justify-center p-4 relative overflow-hidden font-sans">
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

      {/* Main Login Card */}
      <div className="w-full max-w-[440px] relative z-10 animate-in fade-in zoom-in-95 duration-700">
        <div className="bg-card/40 backdrop-blur-2xl border border-white/10 dark:border-white/5 rounded-[40px] p-10 md:p-12 shadow-[0_32px_64px_-16px_rgba(0,0,0,0.2)]">
          
          {/* Header & Branding */}
          <div className="text-center mb-10">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-[22px] bg-gradient-to-br from-primary to-blue-700 shadow-lg shadow-primary/30 mb-6 group transition-transform hover:scale-105 duration-500">
              <Zap className="w-8 h-8 text-white fill-white/20 group-hover:animate-pulse" />
            </div>
            <h1 className="text-3xl font-black tracking-tight mb-2 bg-gradient-to-br from-foreground to-foreground/60 bg-clip-text text-transparent">
              FluxAgent V2
            </h1>
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-primary/10 rounded-full border border-primary/20">
               <span className="w-1.5 h-1.5 bg-primary rounded-full animate-pulse" />
               <p className="text-[10px] font-black uppercase tracking-widest text-primary">
                 Central de Inteligencia
               </p>
            </div>
          </div>

          <SocialLoginButtons />

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-2">
              <label className="text-[11px] font-black uppercase tracking-[0.2em] text-muted-foreground/70 ml-1">
                Identificador de Usuario
              </label>
              <div className="relative group">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground group-focus-within:text-primary transition-colors" />
                <Input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="nombre@empresa.com"
                  className="h-14 pl-12 bg-background/50 border-border/50 rounded-2xl focus:ring-primary/20 focus:border-primary/50 transition-all font-medium"
                />
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between items-center px-1">
                <label className="text-[11px] font-black uppercase tracking-[0.2em] text-muted-foreground/70">
                  Clave de Acceso
                </label>
                <button type="button" className="text-[10px] font-bold text-primary hover:underline">
                  ¿Olvidaste tu clave?
                </button>
              </div>
              <div className="relative group">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground group-focus-within:text-primary transition-colors" />
                <Input
                  type={showPwd ? "text" : "password"}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="h-14 pl-12 pr-12 bg-background/50 border-border/50 rounded-2xl focus:ring-primary/20 focus:border-primary/50 transition-all font-medium"
                />
                <button
                  type="button"
                  onClick={() => setShowPwd(!showPwd)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 p-1 text-muted-foreground hover:text-foreground transition-colors"
                >
                  {showPwd ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>

            <Button
              type="submit"
              disabled={loading}
              className="w-full h-14 bg-primary hover:bg-primary/90 text-primary-foreground rounded-2xl font-black text-sm uppercase tracking-widest shadow-xl shadow-primary/20 group transition-all active:scale-[0.98] mt-6"
            >
              {loading ? (
                <div className="flex items-center gap-3">
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Autenticando...</span>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <span>Acceder al Sistema</span>
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </div>
              )}
            </Button>
          </form>

          {/* Footer Info */}
          <div className="mt-10 pt-8 border-t border-border/50">
            <div className="flex flex-col items-center gap-4">
              <p className="text-xs text-muted-foreground">
                ¿Nuevo en la plataforma?{" "}
                <button 
                  onClick={() => router.push(`/${locale}/register`)}
                  className="text-primary font-black hover:underline"
                >
                  Crea tu cuenta gratis
                </button>
              </p>
              
              <div className="flex items-center gap-6 px-4 py-2 bg-muted/50 rounded-xl border border-border/50">
                <div className="flex items-center gap-2">
                  <Shield className="w-3.5 h-3.5 text-primary" />
                  <span className="text-[10px] font-black text-muted-foreground uppercase tracking-widest">Secure Access</span>
                </div>
                <div className="w-px h-3 bg-border" />
                <div className="flex items-center gap-2">
                  <Activity className="w-3.5 h-3.5 text-green-500" />
                  <span className="text-[10px] font-black text-muted-foreground uppercase tracking-widest">Systems OK</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        {/* Version & Credits */}
        <p className="text-center mt-8 text-[10px] font-bold text-muted-foreground/40 uppercase tracking-[0.3em]">
          FluxAgent Engine v2.4.0 — Enterprise Grade AI
        </p>
      </div>
    </div>
  );
}
