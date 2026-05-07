"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import { Smartphone, RefreshCw, CheckCircle, XCircle, Loader2, Wifi, Timer, Link2, Unlink } from "lucide-react";
import { api } from "@/lib/api";

type ConnStatus = "idle" | "loading" | "qr" | "connected" | "error";

// QR expires every ~30 s in WhatsApp — auto-refresh at 28 s
const QR_TTL = 28;

export default function WhatsAppConnector() {
  const [status, setStatus]         = useState<ConnStatus>("idle");
  const [qrSrc, setQrSrc]           = useState<string | null>(null);
  const [connStatus, setConnStatus]  = useState<string | null>(null);
  const [errorMsg, setErrorMsg]      = useState<string | null>(null);
  const [countdown, setCountdown]    = useState(QR_TTL);
  const [healthData, setHealthData] = useState<any>(null);

  const countdownRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const autoRefreshRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const clearTimers = () => {
    if (countdownRef.current)  clearInterval(countdownRef.current);
    if (autoRefreshRef.current) clearTimeout(autoRefreshRef.current);
  };

  const fetchHealth = useCallback(async () => {
    try {
      const { data } = await api.get("/whatsapp/health", { timeout: 5000 });
      setHealthData(data);
    } catch (e) {
      console.error("Health check failed:", e);
    }
  }, []);

  // ── Fetch QR ─────────────────────────────────────────────────────────────
  const fetchQR = useCallback(async () => {
    clearTimers();
    setStatus("loading");
    setQrSrc(null);
    setErrorMsg(null);

    try {
      // 1. Check if already connected
      const { data: statusData } = await api.get("/whatsapp/instance-status", {
        timeout: 8000,
      });
      const currentConn = statusData.connectionStatus ?? "desconocido";
      setConnStatus(currentConn);

      if (currentConn === "open") {
        setStatus("connected");
        fetchHealth();
        return;
      }

      // 2. Request QR image
      const { data } = await api.get("/whatsapp/qr", {
        timeout: 20_000,
      });
      const base64 = data.base64 ?? data.qr ?? data.code ?? null;

      if (!base64) {
        throw new Error("La API no devolvió un código QR válido.");
      }

      // Evolution API returns full data URI already, handle both cases
      const imgSrc = base64.startsWith("data:") ? base64 : `data:image/png;base64,${base64}`;
      setQrSrc(imgSrc);
      setStatus("qr");
      setCountdown(QR_TTL);

      // ── Countdown timer ────────────────────────────────────────────────
      countdownRef.current = setInterval(() => {
        setCountdown((c) => {
          if (c <= 1) {
            clearInterval(countdownRef.current!);
            return 0;
          }
          return c - 1;
        });
      }, 1000);

      // ── Auto-refresh when expired ──────────────────────────────────────
      autoRefreshRef.current = setTimeout(() => {
        fetchQR();
      }, QR_TTL * 1000);

    } catch (err) {
      const msg = err instanceof Error ? err.message : "Error desconocido";
      setErrorMsg(msg);
      setStatus("error");
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => () => clearTimers(), []);

  // ── Logout ─────────────────────────────────────────────────────────────
  const handleDisconnect = async () => {
    try {
      setStatus("loading");
      await api.delete("/whatsapp/logout");
      setStatus("idle");
      setConnStatus("close");
      setQrSrc(null);
    } catch (err) {
      console.error(err);
      setStatus("error");
    }
  };

  return (
    <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden flex flex-col">
      {/* ── Header ── */}
      <div className="p-5 border-b border-slate-100 flex items-center justify-between bg-slate-50">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 bg-indigo-100 text-indigo-600 rounded-xl">
            <Smartphone className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-800">Canal WhatsApp</h3>
            <p className="text-xxs font-mono text-slate-400 mt-0.5">INSTANCIA: VENTAS_BOT_01</p>
          </div>
        </div>
        
        {connStatus === "open" ? (
          <span className="px-2.5 py-1 rounded-full text-xxs font-bold bg-emerald-50 text-emerald-600 border border-emerald-200 flex items-center">
            <CheckCircle className="w-3 h-3 mr-1" /> CONECTADO
          </span>
        ) : (
          <span className="px-2.5 py-1 rounded-full text-xxs font-bold bg-slate-100 text-slate-500 border border-slate-200 flex items-center">
            <Wifi className="w-3 h-3 mr-1" /> DESCONECTADO
          </span>
        )}
      </div>

      {/* ── Content ── */}
      <div className="p-6 flex-grow flex flex-col items-center justify-center min-h-[300px]">
        {/* IDLE */}
        {status === "idle" && (
          <div className="text-center animate-fadeIn">
            <div className="bg-slate-50 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-4 border border-slate-100 shadow-sm">
              <Smartphone className="w-8 h-8 text-slate-400" />
            </div>
            <h4 className="text-slate-800 font-bold mb-1">Vincular Dispositivo</h4>
            <p className="text-xs text-slate-500 mb-6 max-w-[200px] mx-auto">
              Conecta tu número comercial para que el agente pueda responder automáticamente.
            </p>
            <button 
              onClick={fetchQR}
              className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2 px-6 rounded-xl text-sm transition shadow-sm flex items-center mx-auto"
            >
              <Link2 className="w-4 h-4 mr-2" /> Generar Código QR
            </button>
          </div>
        )}

        {/* LOADING */}
        {status === "loading" && (
          <div className="text-center animate-fadeIn">
            <Loader2 className="w-10 h-10 animate-spin text-indigo-600 mx-auto mb-4" />
            <p className="text-xs font-mono text-slate-500 tracking-wider">COMUNICANDO CON EVOLUTION API...</p>
          </div>
        )}

        {/* QR CODE */}
        {status === "qr" && qrSrc && (
          <div className="text-center animate-fadeIn w-full">
            <div className="bg-white p-4 rounded-2xl shadow-sm border-2 border-indigo-100 inline-block mb-4">
              <img
                src={qrSrc}
                alt="Código QR de WhatsApp"
                className="w-48 h-48 md:w-56 md:h-56 object-contain"
              />
            </div>
            
            <p className="text-xs text-slate-600 mb-4 bg-slate-50 p-2 rounded-lg border border-slate-100">
              Abre WhatsApp → Menú ⋮ → <b>Dispositivos vinculados</b>
            </p>

            <div className="flex items-center justify-center gap-2 bg-amber-50 border border-amber-100 py-2 px-4 rounded-xl mx-auto w-max">
              <Timer className={`w-4 h-4 ${countdown <= 8 ? "text-red-500 animate-pulse" : "text-amber-600"}`} />
              <p className={`text-xs font-bold font-mono ${countdown <= 8 ? "text-red-600" : "text-amber-600"}`}>
                {countdown > 0 ? `EXPIRA EN ${countdown}s` : "ACTUALIZANDO..."}
              </p>
            </div>
          </div>
        )}

        {/* CONNECTED */}
        {status === "connected" && (
          <div className="text-center animate-fadeIn">
            <div className="bg-emerald-50 w-24 h-24 rounded-full flex items-center justify-center mx-auto mb-4 border-4 border-white shadow-md">
              <CheckCircle className="w-12 h-12 text-emerald-500" />
            </div>
            <h4 className="text-xl font-bold text-slate-800 mb-2">Canal Vinculado</h4>
            <p className="text-sm text-slate-500 mb-6 max-w-[220px] mx-auto">
              El agente está monitoreando este número en tiempo real.
            </p>
            {healthData && (
              <div className="bg-slate-50 rounded-xl p-4 mb-4 text-left max-w-[260px] mx-auto border border-slate-100">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-slate-600">Estado del Número</span>
                  <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                    healthData.status === 'healthy' ? 'bg-green-100 text-green-700' :
                    healthData.status === 'degraded' ? 'bg-yellow-100 text-yellow-700' :
                    'bg-red-100 text-red-700'
                  }`}>
                    {healthData.status === 'healthy' ? 'Saludable' : 
                     healthData.status === 'degraded' ? 'Advertencia' : 'Crítico'}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <span className="text-slate-400">Calidad:</span>
                    <span className="ml-1 font-medium">{healthData.quality_rating || 'N/A'}</span>
                  </div>
                  <div>
                    <span className="text-slate-400">Mensajes Hoy:</span>
                    <span className="ml-1 font-medium">{healthData.conversations_today || 0}</span>
                  </div>
                  <div>
                    <span className="text-slate-400">Tasa Entrega:</span>
                    <span className="ml-1 font-medium">{healthData.delivery_rate?.toFixed(1) || 100}%</span>
                  </div>
                  <div>
                    <span className="text-slate-400">Errores:</span>
                    <span className={`ml-1 font-medium ${healthData.error_count_today > 5 ? 'text-red-600' : ''}`}>
                      {healthData.error_count_today || 0}
                    </span>
                  </div>
                </div>
                {healthData.recommendation && (
                  <p className="text-xs text-slate-500 mt-2 pt-2 border-t border-slate-200">
                    💡 {healthData.recommendation}
                  </p>
                )}
              </div>
            )}
            <button 
              onClick={handleDisconnect}
              className="bg-red-50 hover:bg-red-100 text-red-600 border border-red-200 font-bold py-2 px-6 rounded-xl text-sm transition flex items-center mx-auto"
            >
              <Unlink className="w-4 h-4 mr-2" /> Desconectar
            </button>
          </div>
        )}

        {/* ERROR */}
        {status === "error" && (
          <div className="text-center animate-fadeIn">
            <div className="bg-red-50 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-4 border border-red-100">
              <XCircle className="w-10 h-10 text-red-500" />
            </div>
            <h4 className="text-slate-800 font-bold mb-2">Error de Conexión</h4>
            <p className="text-xs text-red-600 mb-6 bg-red-50 p-3 rounded-lg border border-red-100 max-w-[250px] mx-auto">
              {errorMsg}
            </p>
            <button 
              onClick={fetchQR}
              className="bg-slate-800 hover:bg-slate-700 text-white font-bold py-2 px-6 rounded-xl text-sm transition shadow flex items-center mx-auto"
            >
              <RefreshCw className="w-4 h-4 mr-2" /> Reintentar
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
