"use client";

import { useState } from "react";
import { 
  Zap, Save, Check, MousePointerClick, 
  MessageSquare, Play, Database, BrainCircuit,
  Settings2, Plus, CornerDownRight, Workflow
} from "lucide-react";
import { Button } from "@/components/ui/button";

export default function AutomationsPage() {
  const [activeNode, setActiveNode] = useState<number | null>(null);

  // Hardcoded visual representation of a demo workflow
  const nodes = [
    { id: 1, type: "trigger", title: "Mensaje de WhatsApp", desc: "Cuando entra un nuevo chat", icon: MessageSquare, color: "bg-emerald-500", border: "border-emerald-500/50" },
    { id: 2, type: "logic", title: "Validar en Base de Datos", desc: "Buscar Lead por número", icon: Database, color: "bg-blue-500", border: "border-blue-500/50" },
    { id: 3, type: "ai", title: "Agente IA: Valentina", desc: "Procesar intención de compra", icon: BrainCircuit, color: "bg-cyan-500", border: "border-cyan-500/50" },
    { id: 4, type: "action", title: "Agendar Cita", desc: "Crear evento en Calendario", icon: Save, color: "bg-purple-500", border: "border-purple-500/50" },
  ];

  return (
    <div className="h-[calc(100vh-2rem)] flex flex-col bg-black/20 rounded-[2rem] border border-white/5 overflow-hidden animate-fade-in relative">
      
      {/* Background Grid Pattern */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#ffffff05_1px,transparent_1px),linear-gradient(to_bottom,#ffffff05_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_60%_at_50%_50%,#000_70%,transparent_100%)] pointer-events-none"></div>

      {/* Header Bar */}
      <div className="h-16 border-b border-white/5 bg-black/40 backdrop-blur-xl flex items-center justify-between px-6 z-10">
        <div className="flex items-center gap-3">
          <div className="h-8 w-8 rounded-xl bg-cyan-500/20 flex items-center justify-center border border-cyan-500/30">
            <Workflow className="w-4 h-4 text-cyan-400" />
          </div>
          <div>
            <h1 className="text-sm font-bold text-white/90">Flujo de Reserva Automática</h1>
            <p className="text-[10px] text-white/50">Editado hace 2 horas</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" className="h-8 rounded-lg bg-white/5 border-white/10 text-white/70 text-xs px-3 hover:bg-white/10 transition-colors">
            <Play className="w-3 h-3 mr-1.5" /> Probar
          </Button>
          <Button className="h-8 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-black font-bold text-xs px-4 shadow-[0_0_15px_rgba(6,182,212,0.4)] transition-colors">
            <Check className="w-3 h-3 mr-1.5" /> Publicar
          </Button>
        </div>
      </div>

      {/* Canvas Area */}
      <div className="flex-1 flex overflow-hidden relative z-0">
        {/* Tool Palette (Left) */}
        <div className="w-16 border-r border-white/5 bg-black/40 backdrop-blur-md flex flex-col items-center py-4 gap-4 z-10 hidden md:flex">
          {[
            { icon: MessageSquare, color: "text-emerald-400", bg: "bg-emerald-500/10" },
            { icon: BrainCircuit, color: "text-cyan-400", bg: "bg-cyan-500/10" },
            { icon: Database, color: "text-blue-400", bg: "bg-blue-500/10" },
            { icon: Zap, color: "text-amber-400", bg: "bg-amber-500/10" },
            { icon: Save, color: "text-purple-400", bg: "bg-purple-500/10" },
          ].map((tool, idx) => (
            <button key={idx} className={`w-10 h-10 rounded-xl ${tool.bg} border border-white/5 flex items-center justify-center hover:scale-110 transition-transform cursor-grab active:cursor-grabbing`}>
              <tool.icon className={`w-4 h-4 ${tool.color}`} />
            </button>
          ))}
          <div className="w-8 border-t border-white/10 my-2"></div>
          <button className="w-10 h-10 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center hover:bg-white/10 transition-colors">
            <Plus className="w-4 h-4 text-white/60" />
          </button>
        </div>

        {/* Node Editor (Center) */}
        <div className="flex-1 overflow-auto p-12 flex flex-col items-center justify-start min-h-max pb-32">
          
          <div className="bg-cyan-500/10 border border-cyan-500/20 rounded-full px-4 py-1.5 mb-12 flex items-center gap-2 backdrop-blur-sm">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
            <span className="text-xs font-bold text-cyan-400 tracking-wider">CANVAS VISUAL ACTIVO</span>
          </div>

          <div className="flex flex-col items-center w-full max-w-2xl relative">
            {nodes.map((node, index) => (
              <div key={node.id} className="relative w-full flex flex-col items-center">
                
                {/* Visual Node */}
                <div 
                  onClick={() => setActiveNode(node.id)}
                  className={`w-full md:w-[400px] bg-black/60 backdrop-blur-xl border ${activeNode === node.id ? node.border + ' shadow-[0_0_30px_rgba(255,255,255,0.05)]' : 'border-white/10'} rounded-2xl p-4 flex items-center gap-4 cursor-pointer hover:border-white/30 transition-all group relative z-10`}
                  style={activeNode === node.id ? { boxShadow: `0 0 40px ${node.color.replace('bg-', 'rgba(').replace('500', '0.15)')}` } : {}}
                >
                  <div className={`w-12 h-12 rounded-xl ${node.color} flex flex-shrink-0 items-center justify-center shadow-lg`}>
                    <node.icon className="w-5 h-5 text-black" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-bold text-white/40 uppercase tracking-wider">{node.type}</span>
                      <Settings2 className="w-4 h-4 text-white/20 group-hover:text-white/60 transition-colors" />
                    </div>
                    <h3 className="text-sm font-bold text-white/90">{node.title}</h3>
                    <p className="text-xs text-white/50 truncate">{node.desc}</p>
                  </div>

                  {/* Connectors */}
                  {index !== 0 && (
                    <div className="absolute top-0 left-1/2 -mt-1.5 w-3 h-3 bg-black border border-white/20 rounded-full -translate-x-1/2"></div>
                  )}
                  {index !== nodes.length - 1 && (
                    <div className="absolute bottom-0 left-1/2 -mb-1.5 w-3 h-3 bg-black border-2 border-white/50 rounded-full -translate-x-1/2 cursor-crosshair"></div>
                  )}
                </div>

                {/* Arrow connecting nodes */}
                {index !== nodes.length - 1 && (
                  <div className="w-0.5 h-12 bg-gradient-to-b from-white/20 to-white/5 relative z-0 flex items-center justify-center">
                    {/* Add Node Button */}
                    <button className="absolute w-6 h-6 rounded-full bg-black border border-white/10 flex items-center justify-center text-white/40 hover:text-white hover:border-white/40 hover:bg-white/5 transition-all opacity-0 group-hover:opacity-100 scale-0 group-hover:scale-100 delay-100">
                      <Plus className="w-3 h-3" />
                    </button>
                  </div>
                )}
              </div>
            ))}

            <div className="mt-12 opacity-50 flex flex-col items-center">
              <CornerDownRight className="w-6 h-6 text-white/20 mb-2 animate-bounce" />
              <button className="px-6 py-3 rounded-2xl border border-dashed border-white/20 text-sm font-bold text-white/40 hover:text-white/80 hover:bg-white/5 hover:border-white/40 transition-all flex items-center gap-2">
                <Plus className="w-4 h-4" /> Agregar Nuevo Nodo
              </button>
            </div>

          </div>
        </div>

        {/* Properties Panel (Right) */}
        {activeNode && (
          <div className="w-80 border-l border-white/5 bg-black/60 backdrop-blur-xl flex flex-col z-10 animate-in slide-in-from-right-8 hidden lg:flex">
            <div className="h-14 border-b border-white/5 flex items-center px-4">
              <span className="text-xs font-bold text-white/80 uppercase tracking-widest">Propiedades</span>
            </div>
            
            <div className="p-6 space-y-6 flex-1 overflow-auto">
              {activeNode === 3 ? (
                <>
                  <div>
                    <label className="text-[10px] font-bold text-white/40 uppercase mb-2 block">Agente Seleccionado</label>
                    <select className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-sm text-white/90 outline-none focus:border-cyan-500/50 transition-colors appearance-none cursor-pointer">
                      <option>Valentina — Spa Maritza</option>
                      <option>Yanua</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-[10px] font-bold text-white/40 uppercase mb-2 block">Prompt de Contexto</label>
                    <textarea 
                      className="w-full h-32 bg-white/5 border border-white/10 rounded-xl p-3 text-xs text-white/70 outline-none focus:border-cyan-500/50 transition-colors resize-none"
                      defaultValue={"Analiza la intención del usuario para determinar si desea agendar una cita o si solo está pidiendo información general. Pasa la intención al siguiente nodo."}
                    ></textarea>
                  </div>
                  <div>
                    <label className="text-[10px] font-bold text-white/40 uppercase mb-2 block">Variables de Salida</label>
                    <div className="space-y-2">
                      <div className="bg-black border border-white/5 rounded-lg px-3 py-2 text-xs flex justify-between">
                        <span className="text-cyan-400 font-mono">intent</span>
                        <span className="text-white/40">string</span>
                      </div>
                      <div className="bg-black border border-white/5 rounded-lg px-3 py-2 text-xs flex justify-between">
                        <span className="text-cyan-400 font-mono">confidence</span>
                        <span className="text-white/40">number</span>
                      </div>
                    </div>
                  </div>
                </>
              ) : activeNode === 1 ? (
                <>
                  <div>
                    <label className="text-[10px] font-bold text-white/40 uppercase mb-2 block">Conector de Entrada</label>
                    <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl px-4 py-3 text-sm text-emerald-400 font-bold flex items-center gap-2">
                      <MessageSquare className="w-4 h-4" /> Evolution API (WhatsApp)
                    </div>
                  </div>
                  <div>
                    <label className="text-[10px] font-bold text-white/40 uppercase mb-2 mt-6 block">Reglas de Filtrado</label>
                    <div className="bg-white/5 border border-white/10 rounded-xl p-3">
                      <label className="flex items-center gap-3 text-xs text-white/70 cursor-pointer">
                        <input type="checkbox" defaultChecked className="rounded border-white/20 bg-black text-emerald-500 accent-emerald-500" />
                        Ignorar mensajes de grupos
                      </label>
                    </div>
                  </div>
                </>
              ) : (
                <div className="flex flex-col items-center justify-center h-40 text-center text-white/40">
                  <MousePointerClick className="w-8 h-8 mb-3 opacity-50" />
                  <p className="text-sm">Configuración avanzada para este tipo de nodo</p>
                </div>
              )}
            </div>
            
            <div className="p-4 border-t border-white/5">
              <Button className="w-full bg-white/10 hover:bg-white/20 text-white rounded-xl">
                Aplicar Cambios
              </Button>
            </div>
          </div>
        )}
      </div>

    </div>
  );
}
