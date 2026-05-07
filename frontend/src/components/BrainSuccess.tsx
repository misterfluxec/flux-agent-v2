"use client";

import { useEffect, useState } from "react";
import { Brain } from "lucide-react";

interface BrainSuccessProps {
  show: boolean;
  onDone?: () => void;
}

export default function BrainSuccess({ show, onDone }: BrainSuccessProps) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (show) {
      setVisible(true);
      const t = setTimeout(() => { setVisible(false); onDone?.(); }, 3500);
      return () => clearTimeout(t);
    }
  }, [show, onDone]);

  if (!visible) return null;

  return (
    <div
      className="animate-fade"
      style={{
        position: "fixed", inset: 0, zIndex: 999,
        display: "flex", alignItems: "center", justifyContent: "center",
        background: "rgba(0,0,0,0.45)", backdropFilter: "blur(6px)",
      }}
    >
      <div
        style={{
          background: "var(--card)", borderRadius: 24,
          padding: "48px 56px", textAlign: "center",
          boxShadow: "0 25px 60px rgb(0 0 0 / 0.3)",
          border: "1px solid var(--border)",
          display: "flex", flexDirection: "column", alignItems: "center", gap: 20,
          maxWidth: 380, margin: "0 20px",
        }}
      >
        {/* Animated brain */}
        <div className="brain-glow" style={{
          width: 96, height: 96, borderRadius: "50%",
          background: "var(--primary-light)",
          display: "flex", alignItems: "center", justifyContent: "center",
          border: "2px solid var(--primary-mid)",
        }}>
          <Brain size={48} style={{ color: "var(--primary)" }} />
        </div>

        {/* Particles */}
        <div style={{ position: "relative", marginTop: -16 }}>
          {["✨","🚀","⚡","💡","🎯"].map((emoji, i) => (
            <span
              key={i}
              style={{
                position: "absolute",
                fontSize: 18,
                left: `${[-30, 30, -20, 20, 0][i]}px`,
                top: `${[-20, -15, -30, -25, -35][i]}px`,
                animation: `confetti-drop 1.5s ease-out ${i * 0.15}s both`,
              }}
            >
              {emoji}
            </span>
          ))}
        </div>

        <div>
          <p style={{ fontSize: 22, fontWeight: 800, color: "var(--foreground)", margin: "0 0 8px" }}>
            ¡Tu agente ahora es más inteligente! 🚀
          </p>
          <p style={{ fontSize: 14, color: "var(--muted-foreground)", margin: 0 }}>
            Los vectores han sido guardados en la base de datos.<br />
            El cerebro está listo para responder con este nuevo conocimiento.
          </p>
        </div>

        {/* Progress bar that drains */}
        <div style={{ width: "100%", height: 4, background: "var(--secondary)", borderRadius: 10, overflow: "hidden" }}>
          <div style={{
            height: "100%", background: "var(--primary)",
            borderRadius: 10,
            animation: "brain-drain 3.5s linear forwards",
          }} />
        </div>

        <style>{`
          @keyframes brain-drain {
            from { width: 100%; }
            to   { width: 0%; }
          }
          @keyframes confetti-drop {
            0%   { opacity: 1; transform: translateY(0) scale(1) rotate(0deg); }
            100% { opacity: 0; transform: translateY(-40px) scale(1.5) rotate(30deg); }
          }
        `}</style>
      </div>
    </div>
  );
}
