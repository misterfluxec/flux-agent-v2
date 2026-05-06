'use client';

import { useState, useRef, useEffect } from 'react';
import { useTranslations } from 'next-intl';
import { Mic, MicOff, Loader2, AlertTriangle } from 'lucide-react';

interface VoiceTestClientProps {
  tenantId: string;
  wsUrl?: string; // Default: `ws://${window.location.host}/api/v1/sales/voice/stream`
}

export function VoiceTestClient({ tenantId, wsUrl }: VoiceTestClientProps) {
  const t = useTranslations('voice');
  const [isConnected, setIsConnected] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [latency, setLatency] = useState<number | null>(null);
  
  const wsRef = useRef<WebSocket | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const lastSentTimeRef = useRef<number | null>(null);

  // Limpiar recursos al desmontar
  useEffect(() => {
    return () => cleanup();
  }, []);

  const cleanup = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.close();
    }
    if (processorRef.current) {
      processorRef.current.disconnect();
    }
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(track => track.stop());
    }
    if (audioContextRef.current?.state !== 'closed') {
      audioContextRef.current?.close();
    }
    setIsConnected(false);
    setIsRecording(false);
  };

  const connect = async () => {
    try {
      setError(null);
      
      // 1. Obtener stream de micrófono con mitigación de eco/ruido
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          channelCount: 1, // Mono
          sampleRate: 16000 // Solicitar 16kHz directamente si el navegador lo permite
        }
      });
      mediaStreamRef.current = stream;

      // 2. Configurar AudioContext a 16kHz (crítico para Pipecat/Whisper)
      const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
      audioContextRef.current = new AudioContextClass({ sampleRate: 16000 });
      const source = audioContextRef.current.createMediaStreamSource(stream);

      // 3. ScriptProcessor para extraer PCM16 (deprecated pero funcional para V1)
      // ⚠️ Migrar a AudioWorklet en V2 para evitar bloqueos del hilo principal
      processorRef.current = audioContextRef.current.createScriptProcessor(2048, 1, 1);
      source.connect(processorRef.current);
      processorRef.current.connect(audioContextRef.current.destination);

      // 4. Conectar WebSocket con autenticación (JWT en query param)
      const token = localStorage.getItem('token') || '';
      
      // Determinar ws:// o wss:// según si la página cargó con http o https
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const defaultWsUrl = `${protocol}//${window.location.host}/api/v1/sales/voice/stream`;
      
      const url = wsUrl || defaultWsUrl;
      const ws = new WebSocket(`${url}?tenant_id=${tenantId}&token=${token}`);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        console.log('✅ Voice WebSocket connected');
      };

      ws.onmessage = (event) => {
        // Medir latencia roundtrip
        if (lastSentTimeRef.current) {
          const roundtrip = Date.now() - lastSentTimeRef.current;
          setLatency(roundtrip);
          lastSentTimeRef.current = null;
        }

        try {
          const msg = JSON.parse(event.data);
          if (msg.type === 'audio' && msg.data) {
            // Decodificar Base64 → PCM16 → reproducir
            const pcmBytes = atob(msg.data);
            const pcmData = new Int16Array(pcmBytes.length / 2);
            for (let i = 0; i < pcmData.length; i++) {
              pcmData[i] = pcmBytes.charCodeAt(i * 2) | 
                          (pcmBytes.charCodeAt(i * 2 + 1) << 8);
            }
            playPcm16(pcmData);
          } else if (msg.type === 'error') {
            setError(msg.message || 'Error del servidor');
          }
        } catch (e) {
          console.error('Failed to parse voice message:', e);
        }
      };

      ws.onerror = (err) => {
        console.error('WebSocket error:', err);
        setError(t('connection_error'));
        cleanup();
      };

      ws.onclose = () => {
        setIsConnected(false);
        setIsRecording(false);
      };

      // 5. Procesar audio entrante del micrófono
      processorRef.current.onaudioprocess = (e) => {
        if (!isRecording || ws?.readyState !== WebSocket.OPEN) return;

        const input = e.inputBuffer.getChannelData(0);
        // Convertir Float32 (-1 a 1) → Int16 (-32768 a 32767)
        const pcm16 = new Int16Array(input.length);
        for (let i = 0; i < input.length; i++) {
          pcm16[i] = Math.max(-32768, Math.min(32767, Math.floor(input[i] * 32768)));
        }

        // Base64 encode + enviar como JSON
        const base64 = btoa(String.fromCharCode(...new Uint8Array(pcm16.buffer)));
        lastSentTimeRef.current = Date.now();
        ws.send(JSON.stringify({ type: 'audio', data: base64 }));
      };

    } catch (err: any) {
      console.error('Voice setup failed:', err);
      setError(err.message || t('setup_error'));
      cleanup();
    }
  };

  const playPcm16 = (pcmData: Int16Array) => {
    if (!audioContextRef.current) return;
    
    // Crear AudioBuffer para reproducción
    const audioBuffer = audioContextRef.current.createBuffer(1, pcmData.length, 16000);
    const channelData = audioBuffer.getChannelData(0);
    
    // Convertir Int16 → Float32 para Web Audio API
    for (let i = 0; i < pcmData.length; i++) {
      channelData[i] = pcmData[i] / 32768;
    }
    
    const source = audioContextRef.current.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(audioContextRef.current.destination);
    source.start();
  };

  const toggleRecording = () => {
    if (isRecording) {
      setIsRecording(false);
    } else if (wsRef.current?.readyState === WebSocket.OPEN) {
      setIsRecording(true);
    }
  };

  return (
    <div className="max-w-md mx-auto p-6 bg-card border border-border rounded-xl space-y-4">
      <h3 className="text-lg font-semibold">{t('title')}</h3>
      
      {/* Estado de conexión */}
      <div className="flex items-center gap-2 text-sm">
        <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
        <span className={isConnected ? 'text-green-400' : 'text-red-400'}>
          {isConnected ? t('connected') : t('disconnected')}
        </span>
        {latency !== null && isConnected && (
          <span className="text-xs text-muted-foreground ml-2">
            {t('latency')}: {latency}ms
          </span>
        )}
      </div>

      {/* Botón principal */}
      <button
        onClick={isConnected ? toggleRecording : connect}
        disabled={!isConnected && isRecording}
        className={`w-full py-3 rounded-lg font-medium flex items-center justify-center gap-2 transition ${
          isConnected 
            ? isRecording 
              ? 'bg-red-500/20 text-red-400 hover:bg-red-500/30' 
              : 'bg-green-500/20 text-green-400 hover:bg-green-500/30'
            : 'bg-primary text-primary-foreground hover:bg-primary/90'
        }`}
      >
        {isConnected ? (
          isRecording ? (
            <><MicOff className="w-4 h-4" /> {t('stop_recording')}</>
          ) : (
            <><Mic className="w-4 h-4" /> {t('start_recording')}</>
          )
        ) : (
          <><Loader2 className={`w-4 h-4 ${isRecording ? 'animate-spin' : ''}`} /> {t('connecting')}</>
        )}
      </button>

      {/* Mensajes de error */}
      {error && (
        <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-sm text-red-400 flex items-start gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
          {error}
        </div>
      )}

      {/* Notas técnicas */}
      <div className="text-xs text-muted-foreground space-y-1 pt-2 border-t border-border">
        <p>• {t('format_note')}</p>
        <p>• {t('latency_note')}</p>
        <p>• {t('mobile_note')}</p>
      </div>
    </div>
  );
}
