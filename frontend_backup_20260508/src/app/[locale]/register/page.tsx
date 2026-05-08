"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useLocale, useTranslations } from 'next-intl';
import { Eye, EyeOff, Zap, Shield, Activity, Sun, Moon, ArrowRight, Lock, Mail, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";
import SocialLoginButtons from "@/components/auth/SocialLoginButtons";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:9000";

export default function RegisterPage() {
  const router = useRouter();
  const locale = useLocale();
  const t = useTranslations('auth.register') || ((key: string) => key); // Fallback if translations don't exist
  
  const [name, setName] = useState("");
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
      const resp = await fetch(`${BACKEND_URL}/api/v1/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          nombre_usuario: name.trim(),
          email: email.trim().toLowerCase(), 
          password: password 
        }),
      });

      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        let errorMessage = 'Error en el Registro';
        let errorDescription = 'No pudimos crear tu cuenta. Por favor, verifica tus datos.';
        
        if (resp.status === 400 || resp.status === 409) {
           errorMessage = 'Usuario Existente';
           errorDescription = 'El email ya está registrado. Intenta iniciar sesión.';
        } else if (resp.status >= 500) {
          errorMessage = 'Error del Servidor';
          errorDescription = 'Estamos teniendo problemas técnicos. Intenta nuevamente en unos minutos.';
        }
        
        toast.error(errorMessage, {
          description: errorDescription,
          duration: 5000,
        });
        setLoading(false);
        return;
      }

      // Si el registro es exitoso, iniciar sesión automáticamente o redirigir
      const data = await resp.json() as any;
      if (data.access_token) {
        localStorage.setItem("flux_token", data.access_token);
        localStorage.setItem("flux_tenant_id", data.usuario?.tenant_id || 'default');
        document.cookie = `auth_token=${data.access_token}; path=/; max-age=86400; SameSite=lax`;
        router.push(`/${locale}/dashboard`);
      } else {
        toast.success("Cuenta Creada", { description: "Ahora puedes iniciar sesión con tus credenciales." });
        router.push(`/${locale}/login`);
      }
    } catch {
      toast.error('Error Crítico', { description: 'No se pudo conectar con el servidor.' });
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

      {/* Main Register Card */}
      <div className="w-full max-w-md relative z-10 animate-in fade-in zoom-in-95 duration-700">
        <div className="bg-card/40 backdrop-blur-2xl border border-white/10 dark:border-white/5 rounded-[40px] p-10 md:p-12 shadow-[0_32px_64px_-16px_rgba(0,0,0,0.2)]">
          
          {/* Header & Branding */}
          <div className="text-center mb-10">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-[22px] bg-gradient-to-br from-primary to-blue-700 shadow-lg shadow-primary/30 mb-6 group transition-transform hover:scale-105 duration-500">
              <Zap className="w-8 h-8 text-white fill-white/20 group-hover:animate-pulse" />
            </div>
            <h1 className="text-3xl font-black tracking-tight mb-2 bg-gradient-to-br from-purple-400 to-cyan-400 bg-clip-text text-transparent">
              Crear Cuenta
            </h1>
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-primary/10 rounded-full border border-primary/20">
               <span className="w-1.5 h-1.5 bg-primary rounded-full animate-pulse" />
               <p className="text-[10px] font-black uppercase tracking-widest text-primary">
                 Obtén Súper Poderes
               </p>
            </div>
          </div>

          <SocialLoginButtons />

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-2">
              <label className="text-[11px] font-black uppercase tracking-[0.2em] text-muted-foreground/70 ml-1">
                Nombre Completo
              </label>
              <div className="relative group">
                <User className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground group-focus-within:text-primary transition-colors" />
                <Input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Ej: Elon Musk"
                  className="h-14 pl-12 bg-background/50 border-border/50 rounded-2xl focus:ring-primary/20 focus:border-primary/50 transition-all font-medium"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-[11px] font-black uppercase tracking-[0.2em] text-muted-foreground/70 ml-1">
                Correo Electrónico
              </label>
              <div className="relative group">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground group-focus-within:text-primary transition-colors" />
                <Input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="correo@empresa.com"
                  className="h-14 pl-12 bg-background/50 border-border/50 rounded-2xl focus:ring-primary/20 focus:border-primary/50 transition-all font-medium"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-[11px] font-black uppercase tracking-[0.2em] text-muted-foreground/70 ml-1">
                Contraseña Segura
              </label>
              <div className="relative group">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground group-focus-within:text-primary transition-colors" />
                <Input
                  type={showPwd ? "text" : "password"}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
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
                  <span>Configurando Entorno...</span>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <span>Registrar Cuenta</span>
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </div>
              )}
            </Button>
          </form>

          {/* Footer Info */}
          <div className="mt-10 pt-8 border-t border-border/50">
            <div className="flex flex-col items-center gap-4">
              <p className="text-xs text-muted-foreground">
                ¿Ya tienes una cuenta?{" "}
                <button 
                  onClick={() => router.push(`/${locale}/login`)}
                  className="text-primary font-black hover:underline"
                >
                  Iniciar Sesión
                </button>
              </p>
              
              <div className="flex items-center gap-6 px-4 py-2 bg-muted/50 rounded-xl border border-border/50">
                <div className="flex items-center gap-2">
                  <Shield className="w-3.5 h-3.5 text-primary" />
                  <span className="text-[10px] font-black text-muted-foreground uppercase tracking-widest">Datos Encriptados</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        {/* Version & Credits */}
        <p className="text-center mt-8 text-[10px] font-bold text-muted-foreground/40 uppercase tracking-[0.3em]">
          FluxAgent OS v2.0 - Premium Edition
        </p>
      </div>
    </div>
  );
}
