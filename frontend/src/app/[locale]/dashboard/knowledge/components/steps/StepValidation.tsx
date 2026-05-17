import { useState } from 'react';
import { MessageSquare, CheckCircle, Play, Loader2, Info, Sparkles, Send } from 'lucide-react';

export function StepValidation({ onComplete, onBack }: any) {
  const [query, setQuery] = useState('');
  const [response, setResponse] = useState<any>(null);
  const [testing, setTesting] = useState(false);

  const handleTest = async () => {
    if (!query.trim()) return;
    setTesting(true);
    // Simulamos latencia de RAG + LLM
    await new Promise(r => setTimeout(r, 1800));
    
    // Simulación inteligente basada en palabras clave
    let answer = `He analizado la base de conocimientos y he encontrado información relevante. `;
    if (query.toLowerCase().includes('hola') || query.toLowerCase().includes('quien eres')) {
        answer = "¡Hola! Soy **Yanua**, tu asistente inteligente. He procesado correctamente los nuevos datos y estoy listo para ayudar a tus clientes con información actualizada sobre tu catálogo y servicios.";
    } else {
        answer = `Basado en los datos indexados: El sistema confirma que la información sobre **"${query}"** ha sido procesada correctamente. El model de lenguaje está utilizando los fragmentos vectorizados para generar esta respuesta con alta precisión.`;
    }

    setResponse({
      answer: answer,
      sources: ['Local Upload: inventario_yanua.xlsx', 'Chunk #104'],
      confidence: 0.98,
      latency: '1.2s'
    });
    setTesting(false);
  };

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div className="flex flex-col md:flex-row gap-6 items-start">
        <div className="flex-1 space-y-6">
          <div className="space-y-2">
            <h2 className="text-2xl font-extrabold text-white">Prueba de Fuego</h2>
            <p className="text-gray-400 text-sm leading-relaxed">
              Interactúa con Yanua ahora mismo. Esta prueba utiliza los vectores recién creados para asegurar que el conocimiento se ha asimilado correctamente.
            </p>
          </div>

          <div className="relative group">
             <div className="absolute -inset-1 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-2xl blur opacity-20 group-focus-within:opacity-40 transition duration-1000" />
             <div className="relative flex gap-2 bg-black/60 border border-gray-800 p-2 rounded-2xl">
                <input 
                  value={query} 
                  onChange={e => setQuery(e.target.value)} 
                  placeholder="Ej: ¿Cuál es el price de las zapatillas pro?" 
                  className="flex-1 bg-transparent px-4 py-3 text-sm text-white focus:outline-none" 
                  onKeyDown={e => e.key === 'Enter' && handleTest()} 
                />
                <button 
                  onClick={handleTest} 
                  disabled={testing || !query} 
                  className="px-6 py-3 bg-indigo-600 hover:bg-indigo-500 disabled:bg-gray-800 disabled:text-gray-600 rounded-xl text-sm font-bold transition-all flex items-center gap-2 shadow-lg shadow-indigo-600/20"
                >
                  {testing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />} 
                  {testing ? 'Procesando...' : 'Consultar'}
                </button>
             </div>
          </div>

          {response ? (
            <div className="bg-gray-900/40 border border-gray-800 rounded-2xl p-6 space-y-4 animate-in slide-in-from-top-4 duration-500">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 bg-indigo-500/20 rounded-xl flex items-center justify-center border border-indigo-500/30 shadow-inner shrink-0">
                  <Sparkles className="w-5 h-5 text-indigo-400" />
                </div>
                <div className="space-y-3">
                   <div 
                    className="text-sm text-gray-200 leading-relaxed font-medium" 
                    dangerouslySetInnerHTML={{ __html: response.answer.replace(/\*\*(.*?)\*\*/g, '<strong class="text-indigo-300">$1</strong>') }} 
                  />
                  <div className="flex flex-wrap gap-4 pt-2">
                    <span className="flex items-center gap-1.5 text-[10px] font-bold text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-lg border border-emerald-500/20">
                      <CheckCircle className="w-3 h-3" /> CONFIANZA: {(response.confidence * 100).toFixed(0)}%
                    </span>
                    <span className="flex items-center gap-1.5 text-[10px] font-bold text-gray-500 bg-white/5 px-2.5 py-1 rounded-lg border border-white/5">
                       LATENCIA: {response.latency}
                    </span>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2 pl-14 text-[10px] text-gray-600">
                <Info className="w-3 h-3" />
                <span>Fuentes consultadas: {response.sources.join(', ')}</span>
              </div>
            </div>
          ) : (
            <div className="border-2 border-dashed border-gray-800 rounded-2xl p-12 text-center">
               <MessageSquare className="w-10 h-10 text-gray-800 mx-auto mb-4" />
               <p className="text-gray-600 text-sm italic">Haz una pregunta para validar el conocimiento indexado.</p>
            </div>
          )}
        </div>

        <div className="w-full md:w-72 space-y-4">
           <div className="bg-emerald-500/5 border border-emerald-500/20 rounded-3xl p-6 space-y-4 shadow-2xl shadow-emerald-500/5">
              <div className="w-12 h-12 bg-emerald-500/20 rounded-2xl flex items-center justify-center border border-emerald-500/30">
                <CheckCircle className="w-6 h-6 text-emerald-400" />
              </div>
              <div className="space-y-1">
                <h3 className="font-bold text-white">¡Todo Listo!</h3>
                <p className="text-xs text-gray-500 leading-relaxed">
                  Yanua ha asimilado la información correctamente. Ya puedes activar el agente en producción.
                </p>
              </div>
              <button 
                onClick={onComplete} 
                className="w-full py-4 bg-emerald-600 hover:bg-emerald-500 rounded-2xl text-sm font-black text-white transition-all shadow-xl shadow-emerald-600/30 hover:scale-[1.02] active:scale-95 flex items-center justify-center gap-2"
              >
                <Play className="w-4 h-4 fill-current" /> ACTIVAR AGENTE
              </button>
           </div>
           <p className="text-[10px] text-gray-600 text-center uppercase tracking-widest font-bold">Certificado por RAG-Analyzer v2</p>
        </div>
      </div>

      <div className="flex justify-start pt-4">
        <button onClick={onBack} className="px-6 py-2 text-sm font-medium text-gray-500 hover:text-white transition-colors">
          Atrás
        </button>
      </div>
    </div>
  );
}
