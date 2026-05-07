import { useEffect, useState } from 'react';
import { Loader2, CheckCircle, Terminal, Cpu, Database, CloudUpload, Search } from 'lucide-react';

const STAGES = [
  { id: 'extract', label: 'Extracción de conocimiento', icon: CloudUpload },
  { id: 'vectorize', label: 'Vectorización semántica (Ollama)', icon: Cpu },
  { id: 'index', label: 'Indexación en Base Vectorial', icon: Database },
  { id: 'verify', label: 'Optimización del RAG', icon: Search }
];

export function StepProcessing({ jobId, status, progress, onBack }: any) {
  const [currentStage, setCurrentStage] = useState(0);
  const [logs, setLogs] = useState<string[]>([]);

  useEffect(() => {
    // Simulamos avance de etapas basado en el progreso si no tenemos estados detallados del backend
    if (progress > 25 && currentStage === 0) setCurrentStage(1);
    if (progress > 50 && currentStage === 1) setCurrentStage(2);
    if (progress > 85 && currentStage === 2) setCurrentStage(3);
    
    // Log dinámico
    const labels = ["Leyendo estructura de archivos...", "Generando embeddings con nomic-embed-text...", "Almacenando vectores en pgvector...", "Verificando consistencia del índice..."];
    if (progress > 0 && progress < 100) {
      const newLog = `[${new Date().toLocaleTimeString()}] ${labels[currentStage]} (${progress}%)`;
      if (logs[logs.length - 1] !== newLog) {
        setLogs(prev => [...prev.slice(-5), newLog]);
      }
    }
  }, [progress, currentStage]);

  return (
    <div className="space-y-8 animate-in fade-in zoom-in-95 duration-700">
      <div className="text-center space-y-2">
        <h2 className="text-2xl font-extrabold text-white tracking-tight">Procesando Conocimiento</h2>
        <p className="text-gray-400 text-sm">Yanua está aprendiendo de tus datos. Esto puede tomar unos segundos.</p>
      </div>

      <div className="max-w-2xl mx-auto space-y-8">
        {/* Progress Circle & Percentage */}
        <div className="relative flex justify-center">
          <div className="relative w-40 h-40">
             <svg className="w-full h-full transform -rotate-90">
              <circle cx="80" cy="80" r="70" stroke="currentColor" strokeWidth="8" fill="transparent" className="text-gray-800" />
              <circle 
                cx="80" cy="80" r="70" stroke="currentColor" strokeWidth="8" fill="transparent" 
                strokeDasharray={440} 
                strokeDashoffset={440 - (440 * progress) / 100} 
                className="text-indigo-500 transition-all duration-500 ease-out" 
                strokeLinecap="round"
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-4xl font-black text-white">{progress}%</span>
              <span className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">Sincronizando</span>
            </div>
          </div>
          {/* Ambient Glow */}
          <div className="absolute inset-0 bg-indigo-500/10 rounded-full blur-[80px] -z-10 animate-pulse" />
        </div>

        {/* Stages Grid */}
        <div className="grid grid-cols-1 gap-3">
          {STAGES.map((stage, i) => (
            <div key={stage.id} className={`flex items-center gap-4 p-4 rounded-2xl border-2 transition-all duration-500 ${
              i < currentStage 
                ? 'border-emerald-500/30 bg-emerald-500/5 opacity-60' 
                : i === currentStage 
                  ? 'border-indigo-500/40 bg-indigo-500/10 shadow-[0_0_20px_-5px_rgba(99,102,241,0.2)]' 
                  : 'border-gray-800 bg-gray-900/20 opacity-40'
            }`}>
              <div className={`p-2 rounded-xl border ${
                i < currentStage ? 'bg-emerald-500/20 border-emerald-500/30 text-emerald-400' :
                i === currentStage ? 'bg-indigo-500/20 border-indigo-500/30 text-indigo-400' : 'bg-gray-800 border-gray-700 text-gray-600'
              }`}>
                {i < currentStage ? <CheckCircle className="w-5 h-5" /> : <stage.icon className={`w-5 h-5 ${i === currentStage ? 'animate-pulse' : ''}`} />}
              </div>
              <div className="flex-1">
                <span className={`text-sm font-bold ${i <= currentStage ? 'text-white' : 'text-gray-600'}`}>{stage.label}</span>
                {i === currentStage && (
                   <div className="flex gap-1 mt-1">
                      <div className="w-1 h-1 bg-indigo-500 rounded-full animate-bounce [animation-delay:-0.3s]" />
                      <div className="w-1 h-1 bg-indigo-500 rounded-full animate-bounce [animation-delay:-0.15s]" />
                      <div className="w-1 h-1 bg-indigo-500 rounded-full animate-bounce" />
                   </div>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Console Logs */}
        <div className="bg-black/80 rounded-2xl border border-gray-800 p-5 font-mono text-[10px] relative overflow-hidden shadow-2xl">
          <div className="flex items-center gap-2 mb-3 text-gray-500 border-b border-gray-800 pb-2">
            <Terminal className="w-3 h-3" />
            <span className="uppercase tracking-widest font-bold">Consola de entrenamiento</span>
          </div>
          <div className="space-y-1.5 h-20 overflow-y-auto">
            {logs.length === 0 && <p className="text-gray-700 italic">Esperando inicialización del túnel...</p>}
            {logs.map((l, i) => (
              <p key={i} className="flex gap-3">
                <span className="text-indigo-500/50 shrink-0">➜</span>
                <span className="text-gray-400">{l}</span>
              </p>
            ))}
          </div>
          {/* Scanline Effect */}
          <div className="absolute inset-0 pointer-events-none bg-gradient-to-b from-transparent via-indigo-500/5 to-transparent h-4 w-full animate-scanline" />
        </div>
      </div>

      <div className="flex justify-center pt-4 border-t border-gray-800/50">
        {status === 'failed' ? (
          <button onClick={onBack} className="px-8 py-2.5 bg-rose-600 hover:bg-rose-500 rounded-xl text-sm font-bold transition-all shadow-lg shadow-rose-600/20">
            Ver Error y Reintentar
          </button>
        ) : (
          <p className="text-[10px] text-gray-500 font-medium uppercase tracking-[0.2em] animate-pulse italic">No cierres esta ventana durante el proceso</p>
        )}
      </div>
    </div>
  );
}
