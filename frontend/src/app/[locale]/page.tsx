"use client";

import { useState, useEffect, useRef } from 'react';
import { useTranslations, useLocale } from 'next-intl';
import Link from 'next/link';
import '../landing_web.css';

// --- HIGH-END UI COMPONENTS (Imported from Agent-Build Template) --- //

function BlurWord({ word, trigger }: { word: string; trigger: number }) {
  const letters = word.split("");
  const STAGGER = 45;      
  const DURATION = 500;    
  const GRADIENT_HOLD = STAGGER * letters.length + DURATION + 200;

  const [letterStates, setLetterStates] = useState<{ opacity: number; blur: number }[]>(
    letters.map(() => ({ opacity: 0, blur: 20 }))
  );
  const [showGradient, setShowGradient] = useState(true);
  const framesRef = useRef<number[]>([]);
  const timersRef = useRef<ReturnType<typeof setTimeout>[]>([]);

  useEffect(() => {
    framesRef.current.forEach(cancelAnimationFrame);
    timersRef.current.forEach(clearTimeout);
    framesRef.current = [];
    timersRef.current = [];

    setLetterStates(letters.map(() => ({ opacity: 0, blur: 20 })));
    setShowGradient(true);

    letters.forEach((_, i) => {
      const t = setTimeout(() => {
        const start = performance.now();
        const tick = (now: number) => {
          const progress = Math.min((now - start) / DURATION, 1);
          const eased = 1 - Math.pow(1 - progress, 3);
          setLetterStates(prev => {
            const next = [...prev];
            next[i] = { opacity: eased, blur: 20 * (1 - eased) };
            return next;
          });
          if (progress < 1) {
            const id = requestAnimationFrame(tick);
            framesRef.current.push(id);
          }
        };
        const id = requestAnimationFrame(tick);
        framesRef.current.push(id);
      }, i * STAGGER);
      timersRef.current.push(t);
    });

    const gt = setTimeout(() => setShowGradient(false), GRADIENT_HOLD);
    timersRef.current.push(gt);

    return () => {
      framesRef.current.forEach(cancelAnimationFrame);
      timersRef.current.forEach(clearTimeout);
    };
  }, [trigger, letters.join('')]); // Added letters.join('') to fix exhaustive-deps

  const gradientColors = ["#eca8d6", "#a78bfa", "#67e8f9", "#fbbf24", "#eca8d6"];

  return (
    <>
      {letters.map((char, i) => {
        const colorIndex = (i / Math.max(letters.length - 1, 1)) * (gradientColors.length - 1);
        const lower = Math.floor(colorIndex);
        const upper = Math.min(lower + 1, gradientColors.length - 1);
        const t = colorIndex - lower;

        const hex2rgb = (hex: string) => {
          const r = parseInt(hex.slice(1, 3), 16);
          const g = parseInt(hex.slice(3, 5), 16);
          const b = parseInt(hex.slice(5, 7), 16);
          return [r, g, b];
        };
        const [r1, g1, b1] = hex2rgb(gradientColors[lower]);
        const [r2, g2, b2] = hex2rgb(gradientColors[upper]);
        const r = Math.round(r1 + (r2 - r1) * t);
        const g = Math.round(g1 + (g2 - g1) * t);
        const b = Math.round(b1 + (b2 - b1) * t);

        return (
          <span
            key={i}
            style={{
              display: "inline-block",
              opacity: letterStates[i]?.opacity ?? 0,
              filter: `blur(${letterStates[i]?.blur ?? 20}px)`,
              color: showGradient ? `rgb(${r},${g},${b})` : "white",
              transition: "color 0.4s ease",
            }}
          >
            {char === " " ? "\u00A0" : char}
          </span>
        );
      })}
    </>
  );
}

function ParticleVisualization() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const frameRef = useRef(0);
  const mouseRef = useRef({ x: 0.5, y: 0.5 });

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const resize = () => {
      const rect = canvas.getBoundingClientRect();
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      ctx.scale(dpr, dpr);
    };
    resize();
    window.addEventListener("resize", resize);

    const handleMouseMove = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      mouseRef.current = {
        x: (e.clientX - rect.left) / rect.width,
        y: (e.clientY - rect.top) / rect.height,
      };
    };
    canvas.addEventListener("mousemove", handleMouseMove);

    const COUNT = 70;
    const particles = Array.from({ length: COUNT }, (_, i) => {
      const seed = i * 1.618;
      return {
        bx: ((seed * 127.1) % 1),
        by: ((seed * 311.7) % 1),
        phase: seed * Math.PI * 2,
        speed: 0.4 + (seed % 0.4),
        radius: 1.2 + (seed % 2.2),
      };
    });

    let time = 0;
    const render = () => {
      const rect = canvas.getBoundingClientRect();
      const w = rect.width;
      const h = rect.height;

      ctx.clearRect(0, 0, w, h);

      const mx = mouseRef.current.x;
      const my = mouseRef.current.y;

      particles.forEach((p) => {
        const flowX = Math.sin(time * p.speed * 0.4 + p.phase) * 38;
        const flowY = Math.cos(time * p.speed * 0.3 + p.phase * 0.7) * 24;

        const bx = p.bx * w;
        const by = p.by * h;
        const dx = p.bx - mx;
        const dy = p.by - my;
        const dist = Math.sqrt(dx * dx + dy * dy);
        const influence = Math.max(0, 1 - dist * 2.8);

        const x = bx + flowX + influence * Math.cos(time + p.phase) * 36;
        const y = by + flowY + influence * Math.sin(time + p.phase) * 36;

        const pulse = Math.sin(time * p.speed + p.phase) * 0.5 + 0.5;
        const alpha = 0.08 + pulse * 0.18 + influence * 0.3;

        ctx.beginPath();
        ctx.arc(x, y, p.radius + pulse * 0.8, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(34, 211, 238, ${alpha})`; // Cyan tinted
        ctx.fill();
      });

      time += 0.016;
      frameRef.current = requestAnimationFrame(render);
    };
    render();

    return () => {
      window.removeEventListener("resize", resize);
      canvas.removeEventListener("mousemove", handleMouseMove);
      cancelAnimationFrame(frameRef.current);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 pointer-events-auto mix-blend-screen"
      style={{ width: "100%", height: "100%" }}
    />
  );
}

function AnimatedNumber({ end, suffix = "", prefix = "" }: { end: number; suffix?: string; prefix?: string }) {
  const [count, setCount] = useState(0);
  const [isScrambling, setIsScrambling] = useState(true);
  const ref = useRef<HTMLDivElement>(null);
  const [hasAnimated, setHasAnimated] = useState(false);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !hasAnimated) {
          setHasAnimated(true);
          const duration = 2500;
          const startTime = performance.now();
          const animate = (currentTime: number) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 4);
            setCount(Math.floor(eased * end));
            setIsScrambling(progress < 0.8);
            if (progress < 1) requestAnimationFrame(animate);
          };
          requestAnimationFrame(animate);
        }
      },
      { threshold: 0.5 }
    );
    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, [end, hasAnimated]);

  const displayValue = count.toLocaleString();

  return (
    <div ref={ref} className="inline-flex items-baseline">
      <span className="text-gray-500 mr-1">{prefix}</span>
      <span className="tabular-nums">
        {displayValue.split("").map((char, i) => (
          <span
            key={i}
            className={`inline-block transition-all duration-150 ${
              isScrambling && char !== "," ? "blur-[2px]" : ""
            }`}
          >
            {char}
          </span>
        ))}
      </span>
      <span className="text-gray-500 ml-1">{suffix}</span>
    </div>
  );
}

function GridBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const timeRef = useRef(0);
  const frameRef = useRef(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const resize = () => {
      const rect = canvas.getBoundingClientRect();
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      ctx.scale(dpr, dpr);
    };
    resize();
    window.addEventListener("resize", resize);

    const render = () => {
      const rect = canvas.getBoundingClientRect();
      const width = rect.width;
      const height = rect.height;
      ctx.clearRect(0, 0, width, height);
      const gridSize = 60;
      const time = timeRef.current;
      for (let x = 0; x < width; x += gridSize) {
        for (let y = 0; y < height; y += gridSize) {
          const wave = Math.sin(x * 0.01 + y * 0.01 + time) * 0.5 + 0.5;
          const size = 1 + wave * 2;
          ctx.beginPath();
          ctx.arc(x, y, size, 0, Math.PI * 2);
          ctx.fillStyle = "rgba(34, 211, 238, 0.05)"; // Cyan tinted
          ctx.fill();
        }
      }
      const pulseY = (time * 30) % height;
      ctx.strokeStyle = "rgba(34, 211, 238, 0.05)";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(0, pulseY);
      ctx.lineTo(width, pulseY);
      ctx.stroke();
      timeRef.current += 0.02;
      frameRef.current = requestAnimationFrame(render);
    };
    render();

    return () => {
      window.removeEventListener("resize", resize);
      cancelAnimationFrame(frameRef.current);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 pointer-events-none"
      style={{ width: "100%", height: "100%" }}
    />
  );
}

function DotGraph({
  color = "cyan",
  height = 32,
  freq1 = 0.35,
  freq2 = 0.12,
  freqT = 0.7,
  speed = 0.025,
  baseline = 0.3,
  amplitude = 0.5,
}: {
  color?: string;
  height?: number;
  freq1?: number;
  freq2?: number;
  freqT?: number;
  speed?: number;
  baseline?: number;
  amplitude?: number;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const frameRef = useRef(0);
  const timeRef = useRef(Math.random() * 100);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const W = canvas.offsetWidth || 300;
    const H = height;
    canvas.width = W * dpr;
    canvas.height = H * dpr;
    ctx.scale(dpr, dpr);

    const render = () => {
      ctx.clearRect(0, 0, W, H);
      const t = timeRef.current;
      const cols = Math.floor(W / 8);

      for (let i = 0; i < cols; i++) {
        const raw = baseline + amplitude * Math.sin(i * freq1 + t) * Math.cos(i * freq2 + t * freqT);
        const v = Math.max(0, Math.min(1, raw));
        const dotY = H - 4 - v * (H - 8);
        const x = i * 8 + 4;
        const alpha = 0.15 + v * 0.55;
        const r = 1.5 + v * 1.2;

        ctx.beginPath();
        ctx.arc(x, dotY, r, 0, Math.PI * 2);
        
        if (color === "cyan") {
          ctx.fillStyle = `rgba(34, 211, 238, ${alpha})`;
        } else if (color === "purple") {
          ctx.fillStyle = `rgba(167, 139, 250, ${alpha})`;
        } else {
          ctx.fillStyle = `rgba(255, 255, 255, ${alpha})`;
        }
        ctx.fill();
      }

      timeRef.current += speed;
      frameRef.current = requestAnimationFrame(render);
    };

    render();
    return () => cancelAnimationFrame(frameRef.current);
  }, [color, height, freq1, freq2, freqT, speed, baseline, amplitude]);

  return (
    <canvas
      ref={canvasRef}
      style={{ width: "100%", height: `${height}px`, display: "block" }}
    />
  );
}

// --- MAIN PAGE CONTENT --- //

function useLandingContent() {
  const t = useTranslations('landing');
  return {
    nav: t.raw('nav'),
    auth: t.raw('auth'),
    hero: t.raw('hero'),
    market: t.raw('market'),
    features: t.raw('features'),
    chat: t.raw('chat'),
    comparison: t.raw('comparison.rows'),
    plans: Object.values(t.raw('plans')),
    marketAlternatives: t.raw('marketAlternatives.items'),
    stats: t.raw('stats.items'),
    footer: t.raw('footer'),
    final_cta: t.raw('final_cta')
  };
}

export default function LandingPage() {
  const locale = useLocale();
  const content = useLandingContent();
  
  // Hero Animation Logic
  const [isHeroVisible, setIsHeroVisible] = useState(false);
  const [wordIndex, setWordIndex] = useState(0);
  const words = locale === 'en' 
    ? ["sell", "negotiate", "scale", "dominate"] 
    : locale === 'pt' 
    ? ["vender", "negociar", "escalar", "dominar"]
    : ["vende", "negocia", "escala", "domina"];

  useEffect(() => {
    setIsHeroVisible(true);
    const interval = setInterval(() => {
      setWordIndex((prev) => (prev + 1) % words.length);
    }, 2500);
    return () => clearInterval(interval);
  }, [words.length]);

  // General Page Logic
  const [isScrolled, setIsScrolled] = useState(false);
  const [chatOpen, setChatOpen] = useState(true); // Open by default to showcase Elio
  const [chatMessages, setChatMessages] = useState([
    { sender: 'agent', text: "Soy Elio, el Agente Comercial de FluxAgent OS. Estoy conectado a la base de datos y puedo cerrar ventas por ti 24/7. ¿Qué necesitas vender hoy?" }
  ]);
  const [chatInput, setChatInput] = useState('');

  useEffect(() => {
    const handleScroll = () => setIsScrolled(window.scrollY > 50);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const handleChatSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim()) return;

    const userMessage = { sender: 'user', text: chatInput };
    setChatMessages(prev => [...prev, userMessage]);
    setChatInput('');

    setTimeout(() => {
      const agentResponses = [
        "Procesando solicitud... Calculando el mejor enfoque de ventas.",
        "Excelente. Puedo crear un flujo para ofrecer eso a tus clientes de Instagram y cobrarles directamente en el chat.",
        "Como Agente Operativo, mi trabajo es asegurarme de que no pierdas ningún cliente mientras duermes. ¿Listo para configurar la integración?"
      ];
      const randomResponse = agentResponses[Math.floor(Math.random() * agentResponses.length)];
      setChatMessages(prev => [...prev, { sender: 'agent', text: randomResponse }]);
    }, 1500);
  };

  const planIcons = ['🌱', '🚀', '🏢'];
  const plansData = content.plans.map((plan: any, idx: number) => ({
    ...plan,
    icon: planIcons[idx]
  }));

  return (
    <div className="min-h-screen bg-black text-white overflow-x-hidden selection:bg-cyan-500/30 font-sans">
      
      {/* Navigation */}
      <nav className={`fixed w-full z-50 transition-all duration-300 ${isScrolled ? 'bg-black/80 backdrop-blur-xl border-b border-white/5 py-4' : 'bg-transparent py-6'}`}>
        <div className="max-w-[1400px] mx-auto px-6 lg:px-12 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <div className="relative w-8 h-8 flex items-center justify-center">
              <img src="/logo.png" alt="FluxAgent OS Logo" className="w-full h-full object-contain" />
            </div>
            <span className="text-xl font-bold tracking-tight text-white">FluxAgent OS</span>
          </div>

          <div className="hidden md:flex gap-8 text-sm font-medium text-gray-400">
            <a href="#features" className="hover:text-white transition-colors">{content.nav.features}</a>
            <a href="#comparativa" className="hover:text-white transition-colors">{content.nav.comparison}</a>
            <a href="#pricing" className="hover:text-white transition-colors">{content.nav.pricing}</a>
          </div>

          <div className="flex items-center gap-4">
            <Link href={`/${locale}/login`} className="text-sm font-semibold text-gray-400 hover:text-white transition-colors hidden sm:block">{content.auth.login}</Link>
            <Link href={`/${locale}/register`} className="relative group px-6 py-2 rounded-full bg-white text-black hover:bg-gray-200 transition-all overflow-hidden text-sm font-bold">
              {content.auth.free_trial.replace('⚡', '').trim()}
            </Link>
            
            <div className="flex items-center gap-2 pl-4 border-l border-white/10">
              {['en', 'es', 'pt'].map((lang) => (
                <Link key={lang} href={`/${lang}`} className={`text-[10px] font-bold uppercase transition-all ${locale === lang ? 'text-white' : 'text-gray-600 hover:text-gray-400'}`}>
                  {lang}
                </Link>
              ))}
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section (Template Integrated) */}
      <section className="relative min-h-screen flex flex-col justify-center items-start overflow-hidden bg-black">
        <div className="absolute inset-0 z-0">
          <video
            autoPlay
            muted
            loop
            playsInline
            className="w-full h-full object-cover object-center opacity-[0.15]"
          >
            <source src="https://hebbkx1anhila5yf.public.blob.vercel-storage.com/bg-hero-0BnFGdr81Ifnj3WbBZoNt1KE4D5DMT.mp4" type="video/mp4" />
          </video>
          <div className="absolute inset-0 bg-gradient-to-r from-black via-black/80 to-transparent" />
          <div className="absolute inset-0 bg-gradient-to-b from-black/20 via-transparent to-black" />
        </div>

        <div className="absolute inset-0 z-[2] overflow-hidden pointer-events-none opacity-20">
          {[...Array(8)].map((_, i) => (
            <div key={`h-${i}`} className="absolute h-px bg-white/10" style={{ top: `${12.5 * (i + 1)}%`, left: 0, right: 0 }} />
          ))}
          {[...Array(12)].map((_, i) => (
            <div key={`v-${i}`} className="absolute w-px bg-white/10" style={{ left: `${8.33 * (i + 1)}%`, top: 0, bottom: 0 }} />
          ))}
        </div>
        
        <div className="relative z-10 w-full max-w-[1400px] mx-auto px-6 lg:px-12 py-32 lg:py-40 flex flex-col lg:flex-row items-center gap-16">
          <div className="lg:w-3/5">
            <div className={`mb-8 transition-all duration-700 ${isHeroVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"}`}>
              <span className="inline-flex items-center gap-3 text-sm font-mono text-cyan-400/80">
                <span className="w-8 h-px bg-cyan-400/30" />
                Inteligencia Comercial Autónoma
              </span>
            </div>
            
            <div className="mb-12">
              <h1 className={`text-left text-[clamp(2.5rem,6vw,5.5rem)] font-bold leading-[1.05] tracking-tight text-white transition-all duration-1000 ${isHeroVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"}`}>
                <span className="block whitespace-nowrap">Tu negocio,</span>
                <span className="block whitespace-nowrap text-gray-400">que ahora </span>
                <span className="block whitespace-nowrap">
                  <span className="relative inline-block">
                    <BlurWord word={words[wordIndex]} trigger={wordIndex} />
                  </span>
                </span>
              </h1>
            </div>

            <p className={`text-xl text-gray-400 leading-relaxed font-light max-w-xl mb-10 transition-all duration-1000 delay-200 ${isHeroVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"}`}>
              {content.hero.subtitle_2}
            </p>

            <div className={`flex gap-4 transition-all duration-1000 delay-300 ${isHeroVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"}`}>
              <Link href={`/${locale}/register`} className="px-8 py-4 bg-white text-black font-bold text-lg rounded-full hover:scale-105 transition-transform shadow-[0_0_40px_rgba(255,255,255,0.15)]">
                {content.hero.cta_activate.replace('⚡', '').trim()}
              </Link>
            </div>
          </div>

          {/* Elio - High-end Sales Showcase */}
          <div className={`lg:w-2/5 w-full relative perspective-1000 transition-all duration-1000 delay-500 ${isHeroVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-12"}`}>
            <div className="relative w-full bg-[#050505]/80 backdrop-blur-2xl border border-white/10 rounded-3xl p-6 shadow-2xl overflow-hidden transform hover:rotate-y-[-2deg] hover:rotate-x-[2deg] transition-transform duration-700">
              
              <div className="flex items-center justify-between mb-6 border-b border-white/5 pb-4">
                <div className="flex items-center gap-4">
                  <div className="relative w-12 h-12 rounded-full overflow-hidden bg-gradient-to-br from-cyan-900 to-black border border-cyan-500/30 flex items-center justify-center">
                    <div className="absolute inset-0 bg-cyan-500/20 blur-md animate-pulse"></div>
                    <span className="relative z-10 text-xl">✨</span>
                  </div>
                  <div>
                    <h3 className="text-white font-bold text-lg leading-none mb-1">Elio</h3>
                    <p className="text-cyan-400 text-xs font-mono">Senior Sales Agent (FluxAgent OS)</p>
                  </div>
                </div>
                <div className="flex gap-1.5">
                  <div className="w-2.5 h-2.5 rounded-full bg-red-500/50"></div>
                  <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/50"></div>
                  <div className="w-2.5 h-2.5 rounded-full bg-green-500/80"></div>
                </div>
              </div>

              <div className="space-y-4 h-[300px] overflow-y-auto pr-2 custom-scrollbar">
                {chatMessages.map((msg, idx) => (
                  <div key={idx} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[85%] px-4 py-3 rounded-2xl text-sm leading-relaxed ${
                      msg.sender === 'user' 
                      ? 'bg-white text-black rounded-tr-sm' 
                      : 'bg-white/5 text-gray-300 border border-white/10 rounded-tl-sm'
                    }`}>
                      {msg.text}
                    </div>
                  </div>
                ))}
              </div>

              <form onSubmit={handleChatSubmit} className="mt-4 relative">
                <input 
                  type="text" 
                  value={chatInput} 
                  onChange={(e) => setChatInput(e.target.value)} 
                  placeholder="Habla con Elio..." 
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-4 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500 transition-colors" 
                />
                <button type="submit" className="absolute right-2 top-1/2 -translate-y-1/2 p-2 bg-white text-black rounded-lg hover:bg-gray-200 transition-colors">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" /></svg>
                </button>
              </form>
            </div>
            
            {/* Ambient glows behind the chat */}
            <div className="absolute -inset-4 bg-gradient-to-r from-cyan-500/20 to-purple-500/20 blur-3xl -z-10 rounded-full mix-blend-screen animate-pulse-slow"></div>
          </div>
        </div>
      </section>

      {/* High-End Features Section (Template Based) */}
      <section id="features" className="relative py-24 lg:py-32 overflow-hidden bg-black">
        <div className="max-w-[1400px] mx-auto px-6 lg:px-12">
          
          <div className="relative mb-24 lg:mb-32">
            <div className="grid lg:grid-cols-12 gap-8 items-end">
              <div className="lg:col-span-7">
                <span className="inline-flex items-center gap-3 text-sm font-mono text-gray-500 mb-6">
                  <span className="w-12 h-px bg-white/30" />
                  {content.features.badge}
                </span>
                <h2 className="text-5xl md:text-7xl lg:text-[90px] font-bold tracking-tight leading-[0.9]">
                  {content.features.title_1}
                  <br />
                  <span className="text-gray-600">{content.features.title_2}</span>
                </h2>
              </div>
              <div className="lg:col-span-5 lg:pb-4">
                <p className="text-xl text-gray-400 leading-relaxed">
                  {content.features.subtitle}
                </p>
              </div>
            </div>
          </div>

          <div className="grid lg:grid-cols-12 gap-4 lg:gap-6">
            <div className="lg:col-span-12 relative bg-[#050505] border border-white/10 min-h-[500px] overflow-hidden group transition-all duration-700 flex rounded-3xl">
              
              <div className="relative flex-1 p-8 lg:p-12">
                <ParticleVisualization />
                <div className="relative z-10">
                  <span className="font-mono text-sm text-cyan-400">01</span>
                  <h3 className="text-3xl lg:text-5xl font-bold mt-4 mb-6 group-hover:translate-x-2 transition-transform duration-500">
                    Sincronización en Tiempo Real
                  </h3>
                  <p className="text-lg text-gray-400 leading-relaxed max-w-md mb-8">
                    El agente se conecta directamente a tu E-commerce o Base de datos. Nunca vende un producto sin stock y siempre ofrece el precio actualizado al milisegundo.
                  </p>
                  <div>
                    <span className="text-5xl lg:text-6xl font-bold">0ms</span>
                    <span className="block text-sm text-gray-500 font-mono mt-2">Latencia de Inventario</span>
                  </div>
                </div>
              </div>

              <div className="hidden lg:block relative w-[42%] shrink-0 bg-gradient-to-br from-white/5 to-transparent border-l border-white/5 flex items-center justify-center">
                <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-cyan-900/20 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-700"></div>
                <div className="relative z-10 w-48 h-48 border border-white/10 rounded-full flex items-center justify-center bg-black/50 backdrop-blur-md">
                   <div className="w-32 h-32 border border-cyan-500/30 rounded-full flex items-center justify-center animate-[spin_10s_linear_infinite]">
                     <div className="w-4 h-4 bg-cyan-400 rounded-full absolute -top-2 blur-[2px]"></div>
                   </div>
                </div>
              </div>
            </div>

            {/* Sub features */}
            {content.features.items.slice(1).map((feature: any, idx: number) => (
              <div key={idx} className="lg:col-span-4 relative bg-[#050505] border border-white/10 p-8 rounded-3xl overflow-hidden hover:bg-white/[0.02] transition-colors">
                <span className="font-mono text-sm text-gray-500">0{idx + 2}</span>
                <h3 className="text-2xl font-bold mt-4 mb-4">{feature.title}</h3>
                <p className="text-gray-400">{feature.description}</p>
                <div className="absolute bottom-0 right-0 w-32 h-32 bg-gradient-to-tl from-white/5 to-transparent rounded-tl-full"></div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* High-End Dynamic Metrics Section */}
      <section className="relative py-24 lg:py-32 overflow-hidden bg-black border-y border-white/5">
        <GridBackground />
        
        <div className="relative z-10 max-w-[1400px] mx-auto px-6 lg:px-12">
          <div className="mb-16">
            <div className="flex items-center gap-4 mb-6">
              <span className="flex items-center gap-2 px-3 py-1 bg-cyan-500/10 text-cyan-400 text-xs font-mono rounded-full border border-cyan-500/20">
                <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
                Métricas del Ecosistema
              </span>
            </div>
            <h2 className="text-4xl md:text-6xl lg:text-[80px] font-bold tracking-tight leading-[0.95]">
              Rendimiento<br />
              <span className="text-gray-600">en tiempo real.</span>
            </h2>
          </div>

          <div className="grid lg:grid-cols-3 gap-6">
            {/* Large metric 1 */}
            <div className="lg:col-span-1 bg-white/[0.02] border border-white/10 p-10 lg:p-14 rounded-3xl hover:bg-white/[0.04] transition-colors group">
              <div className="text-5xl lg:text-6xl font-bold tracking-tight mb-4 text-cyan-400">
                <AnimatedNumber end={1250000} suffix="+" prefix="" />
              </div>
              <div className="mb-6 opacity-50 group-hover:opacity-100 transition-opacity">
                <DotGraph color="cyan" height={36} freq1={0.28} freq2={0.09} freqT={0.5} speed={0.018} baseline={0.35} amplitude={0.55} />
              </div>
              <div className="text-xl text-white font-bold mb-2">Ventas Automatizadas</div>
              <div className="text-sm text-gray-500 font-mono">cerradas por Elio este mes</div>
            </div>

            {/* Metric 2 */}
            <div className="bg-white/[0.02] border border-white/10 p-8 rounded-3xl flex flex-col justify-between hover:bg-white/[0.04] transition-colors group">
              <div className="w-full">
                <div className="text-sm text-gray-500 font-mono mb-2">Tiempo de Respuesta</div>
                <div className="text-lg text-white font-bold mb-3">Latencia Promedio</div>
                <div className="opacity-50 group-hover:opacity-100 transition-opacity">
                  <DotGraph color="white" height={24} freq1={0.45} freq2={0.18} freqT={1.1} speed={0.032} baseline={0.4} amplitude={0.45} />
                </div>
              </div>
              <div className="text-5xl lg:text-6xl font-bold tracking-tight w-full mt-8">
                <AnimatedNumber end={10} suffix="ms" prefix="<" />
              </div>
            </div>

            {/* Metric 3 */}
            <div className="bg-white/[0.02] border border-white/10 p-8 rounded-3xl flex flex-col justify-between hover:bg-white/[0.04] transition-colors group">
              <div className="w-full">
                <div className="text-sm text-gray-500 font-mono mb-2">Seguridad Bancaria</div>
                <div className="text-lg text-white font-bold mb-3">Uptime del Sistema</div>
                <div className="opacity-50 group-hover:opacity-100 transition-opacity">
                  <DotGraph color="purple" height={24} freq1={0.22} freq2={0.07} freqT={0.4} speed={0.015} baseline={0.25} amplitude={0.6} />
                </div>
              </div>
              <div className="text-5xl lg:text-6xl font-bold tracking-tight w-full mt-8 text-purple-400">
                <AnimatedNumber end={99.9} suffix="%" prefix="" />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Tech Stack Marquee (Logos) */}
      <section className="py-12 border-y border-white/5 bg-white/[0.02] relative z-10">
        <div className="max-w-[1400px] mx-auto px-6 overflow-hidden">
          <p className="text-center text-sm font-medium text-gray-500 uppercase tracking-widest mb-8">{content.nav.tech}</p>
          <div className="flex flex-wrap justify-center items-center gap-12 md:gap-24 opacity-50 hover:opacity-100 transition-opacity duration-500">
            <div className="flex items-center gap-3 font-bold text-xl tracking-tight text-white/90"><span className="text-green-500">🔒</span> Seguridad Bancaria</div>
            <div className="flex items-center gap-3 font-bold text-xl tracking-tight text-white/90"><span className="text-blue-500">📱</span> Omnicanalidad</div>
            <div className="flex items-center gap-3 font-bold text-xl tracking-tight text-white/90"><span className="text-purple-500">⚡</span> Sincronización Real</div>
            <div className="flex items-center gap-3 font-bold text-xl tracking-tight text-white/90"><span className="text-cyan-500">🧠</span> Inteligencia Global</div>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="py-24 lg:py-32 px-6 relative z-10 bg-black">
        <div className="max-w-[1400px] mx-auto">
          <div className="mb-20">
            <h2 className="text-5xl md:text-7xl font-bold mb-6 tracking-tight">{content.nav.pricing}</h2>
            <p className="text-xl text-gray-400">Despliega tu inteligencia operativa a una fracción del costo tradicional.</p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {plansData.map((plan: any, index: number) => (
              <div key={index} className={`relative p-10 rounded-3xl transition-all duration-300 ${plan.recommended ? 'bg-[#0a0a0f] border border-cyan-500/30' : 'bg-[#050505] border border-white/10 hover:border-white/20'}`}>
                {plan.recommended && (
                  <div className="absolute top-0 right-10 -translate-y-1/2 px-4 py-1.5 bg-cyan-500 text-black font-bold text-xs uppercase tracking-wider rounded-full">
                    SaaS Estándar
                  </div>
                )}
                <div className="mb-8">
                  <h3 className="text-2xl font-bold mb-2">{plan.name}</h3>
                  <p className="text-gray-400 text-sm">{plan.tagline}</p>
                </div>
                <div className="mb-10">
                  <span className="text-6xl font-bold">${plan.price}</span>
                  <span className="text-gray-500 font-medium ml-2">{plan.period}</span>
                </div>
                <ul className="space-y-4 mb-10">
                  {plan.features.map((feature: string, fIndex: number) => (
                    <li key={fIndex} className="flex items-center gap-3 text-gray-300 text-sm">
                      <div className="w-1.5 h-1.5 rounded-full bg-cyan-400"></div>
                      {feature}
                    </li>
                  ))}
                </ul>
                <Link href={`/${locale}/register`} className={`block w-full py-4 rounded-xl font-bold text-center transition-all ${plan.recommended ? 'bg-white text-black hover:bg-gray-200' : 'bg-white/10 hover:bg-white/20 text-white'}`}>
                  {plan.cta.replace('⚡', '').trim()}
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-24 px-6 relative z-10 border-t border-white/10 bg-[#020202]">
        <div className="max-w-[1400px] mx-auto text-center mb-24">
          <h2 className="text-5xl md:text-8xl font-bold mb-8 tracking-tighter leading-none">
            El Futuro es
            <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-gray-400 to-white">Autónomo.</span>
          </h2>
          <Link href={`/${locale}/register`} className="inline-block px-10 py-5 bg-white text-black rounded-full font-bold text-lg hover:scale-105 transition-transform">
            Inicia con FluxAgent OS
          </Link>
        </div>

        <div className="max-w-[1400px] mx-auto grid md:grid-cols-4 gap-12 border-t border-white/10 pt-16">
          {content.footer.sections.map((section: any, idx: number) => (
            <div key={idx}>
              <h4 className="text-white font-bold mb-6 text-sm uppercase tracking-widest">{section.title}</h4>
              <ul className="space-y-4">
                {section.content.map((item: string, iIdx: number) => (
                  <li key={iIdx} className="text-gray-500 text-sm hover:text-white cursor-pointer transition-colors">{item}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <div className="max-w-[1400px] mx-auto mt-24 flex flex-col md:flex-row justify-between items-center text-gray-600 text-sm border-t border-white/5 pt-8">
          <div>{content.footer.rights}</div>
          <div className="mt-4 md:mt-0 font-mono text-xs">SYS_OPERATIONAL: OK</div>
        </div>
      </footer>

    </div>
  );
}
