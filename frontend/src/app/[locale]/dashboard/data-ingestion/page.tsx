"use client";

import { useState, useEffect } from "react";
import {
  Brain, Upload, Cpu, PackageCheck, Link2, BookOpen,
  FileText, Globe, Sheet, Loader2, CheckCircle2,
  AlertCircle, Package, Search, Edit3, Save, X,
  Users2, ChevronRight, Trash2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import {
  fetchKnowledge, deleteKnowledgeSource, KnowledgeSource,
  fetchProducts, updateProduct, ProductData,
  fetchAgents, AgentResponse,
  uploadDocument, ingestUrl, fetchIngestionStatus,
} from "@/lib/api";

// =============================================================================
// TABS CONFIG
// =============================================================================

const TABS = [
  { id: "learn", label: "Aprender", icon: Upload, desc: "Enséñale a tu IA" },
  { id: "process", label: "Procesar", icon: Cpu, desc: "Estado de ingesta" },
  { id: "validate", label: "Validar", icon: PackageCheck, desc: "Revisa lo aprendido" },
  { id: "assign", label: "Asignar", icon: Link2, desc: "Conecta agente ↔ conocimiento" },
];

// =============================================================================
// MAIN PAGE
// =============================================================================

export default function IntelligencePage() {
  const [activeTab, setActiveTab] = useState("learn");

  return (
    <div className="space-y-6 animate-in fade-in duration-700 pb-12 px-4 md:px-8 max-w-7xl mx-auto pt-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-black tracking-tight text-white/90">
          <span className="text-cyan-400">Inteligencia</span> Empresarial
        </h1>
        <p className="text-white/40 text-sm mt-1">
          Todo lo que tu IA sabe sobre tu negocio — desde la fuente hasta el agente.
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-1 bg-white/[0.02] border border-white/5 rounded-2xl p-1.5">
        {TABS.map((tab, i) => {
          const Icon = tab.icon;
          const active = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex-1 flex items-center justify-center gap-2 py-3 px-4 rounded-xl text-sm font-bold transition-all ${
                active
                  ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/15"
                  : "text-white/30 hover:text-white/50 hover:bg-white/[0.03] border border-transparent"
              }`}
            >
              <Icon className="h-4 w-4" />
              <span className="hidden md:inline">{tab.label}</span>
              {!active && (
                <span className="hidden lg:inline text-[10px] text-white/15 font-normal ml-1">{i + 1}</span>
              )}
            </button>
          );
        })}
      </div>

      {/* Tab Content */}
      <div className="bg-black/40 backdrop-blur-xl border border-white/5 rounded-2xl overflow-hidden min-h-[500px]">
        {activeTab === "learn" && <TabLearn />}
        {activeTab === "process" && <TabProcess />}
        {activeTab === "validate" && <TabValidate />}
        {activeTab === "assign" && <TabAssign />}
      </div>
    </div>
  );
}

// =============================================================================
// TAB 1: APRENDER — Upload sources
// =============================================================================

function TabLearn() {
  const [uploading, setUploading] = useState(false);
  const [urlInput, setUrlInput] = useState("");
  const [lastJobId, setLastJobId] = useState<string | null>(null);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const res = await uploadDocument(file);
      setLastJobId(res.job_id);
      toast.success(`"${file.name}" enviado a procesamiento`);
    } catch {
      toast.error("Error al subir archivo");
    } finally {
      setUploading(false);
    }
  };

  const handleUrlIngest = async () => {
    if (!urlInput.trim()) return;
    setUploading(true);
    try {
      const res = await ingestUrl(urlInput);
      setLastJobId(res.job_id);
      toast.success("URL enviada a procesamiento");
      setUrlInput("");
    } catch {
      toast.error("Error al procesar URL");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="p-6 md:p-8 space-y-6 animate-in fade-in duration-300">
      <div className="flex items-center gap-3 mb-2">
        <div className="h-10 w-10 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center">
          <BookOpen className="h-5 w-5 text-cyan-400" />
        </div>
        <div>
          <h2 className="text-lg font-black text-white">Enséñale a tu IA</h2>
          <p className="text-xs text-white/30">Sube documentos, conecta URLs o importa hojas de cálculo</p>
        </div>
      </div>

      {/* Upload Zone */}
      <label className="block cursor-pointer">
        <div className="border-2 border-dashed border-white/10 hover:border-cyan-500/30 rounded-2xl p-10 text-center transition-all hover:bg-cyan-500/[0.02] group">
          {uploading ? (
            <Loader2 className="h-10 w-10 text-cyan-400 mx-auto animate-spin" />
          ) : (
            <Upload className="h-10 w-10 text-white/15 mx-auto group-hover:text-cyan-400/50 transition-colors" />
          )}
          <p className="text-sm font-bold text-white/50 mt-4 group-hover:text-white/70">
            {uploading ? "Procesando..." : "Arrastra archivos aquí o haz click para seleccionar"}
          </p>
          <p className="text-xs text-white/20 mt-2">PDF, CSV, XLSX, TXT — Máximo 50MB</p>
        </div>
        <input type="file" className="hidden" accept=".pdf,.csv,.xlsx,.txt,.xls" onChange={handleFileUpload} disabled={uploading} />
      </label>

      {/* URL Input */}
      <div className="flex gap-2">
        <div className="flex-1 relative">
          <Globe className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-white/20" />
          <input
            value={urlInput}
            onChange={e => setUrlInput(e.target.value)}
            onKeyDown={e => e.key === "Enter" && handleUrlIngest()}
            placeholder="https://tu-sitio.com/productos..."
            className="w-full bg-white/5 border border-white/10 rounded-xl pl-11 pr-4 py-3 text-sm text-white placeholder:text-white/20 focus:outline-none focus:border-cyan-500/40"
          />
        </div>
        <Button onClick={handleUrlIngest} disabled={uploading || !urlInput.trim()}
          className="bg-cyan-500/20 text-cyan-400 hover:bg-cyan-500/30 rounded-xl px-5 font-bold">
          Ingestar URL
        </Button>
      </div>

      {/* Sources Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { icon: FileText, label: "PDF", desc: "Manuales, catálogos, fichas" },
          { icon: Sheet, label: "Excel / CSV", desc: "Inventarios, precios, listas" },
          { icon: Globe, label: "Web / URL", desc: "Sitios, landing pages" },
          { icon: Brain, label: "Google Sheets", desc: "Hojas dinámicas en la nube" },
        ].map(s => (
          <div key={s.label} className="bg-white/[0.02] border border-white/5 rounded-xl p-4 hover:border-white/10 transition-colors">
            <s.icon className="h-5 w-5 text-white/20 mb-2" />
            <p className="text-xs font-bold text-white/50">{s.label}</p>
            <p className="text-[10px] text-white/20 mt-0.5">{s.desc}</p>
          </div>
        ))}
      </div>

      {lastJobId && (
        <div className="flex items-center gap-2 p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-xl text-xs text-emerald-400 font-medium">
          <CheckCircle2 className="h-4 w-4" />
          Job iniciado: <code className="bg-black/30 px-2 py-0.5 rounded text-[10px]">{lastJobId}</code>
          — Ve a la pestaña "Procesar" para monitorear.
        </div>
      )}
    </div>
  );
}

// =============================================================================
// TAB 2: PROCESAR — Knowledge sources status
// =============================================================================

function TabProcess() {
  const [sources, setSources] = useState<KnowledgeSource[]>([]);
  const [loading, setLoading] = useState(true);
  const [totalChunks, setTotalChunks] = useState(0);

  const load = async () => {
    try {
      setLoading(true);
      const data = await fetchKnowledge();
      setSources(data.fuentes || []);
      setTotalChunks(data.total_chunks || 0);
    } catch {
      toast.error("Error al cargar fuentes");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleDelete = async (nombre: string) => {
    if (!confirm(`¿Eliminar la fuente "${nombre}" y todos sus chunks?`)) return;
    try {
      await deleteKnowledgeSource(nombre);
      toast.success("Fuente eliminada");
      load();
    } catch {
      toast.error("Error al eliminar");
    }
  };

  return (
    <div className="p-6 md:p-8 space-y-5 animate-in fade-in duration-300">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center">
            <Cpu className="h-5 w-5 text-blue-400" />
          </div>
          <div>
            <h2 className="text-lg font-black text-white">Estado de Procesamiento</h2>
            <p className="text-xs text-white/30">{totalChunks} fragmentos procesados en total</p>
          </div>
        </div>
        <Button variant="ghost" onClick={load} className="text-white/30 hover:text-white/60 text-xs font-bold">
          Refrescar
        </Button>
      </div>

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map(i => <div key={i} className="h-16 bg-white/[0.02] rounded-xl animate-pulse" />)}
        </div>
      ) : sources.length === 0 ? (
        <div className="text-center py-16">
          <Cpu className="h-10 w-10 text-white/10 mx-auto mb-3" />
          <p className="text-sm font-bold text-white/40">Sin fuentes procesadas</p>
          <p className="text-xs text-white/20 mt-1">Sube documentos en la pestaña "Aprender" para comenzar.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {sources.map(s => (
            <div key={s.fuente_nombre} className="flex items-center gap-4 px-5 py-4 bg-white/[0.02] border border-white/5 rounded-xl hover:border-white/10 transition-colors group">
              <div className="h-9 w-9 rounded-lg bg-emerald-500/10 flex items-center justify-center">
                {s.fuente_tipo === "pdf" ? <FileText className="h-4 w-4 text-emerald-400" /> :
                 s.fuente_tipo === "url" ? <Globe className="h-4 w-4 text-blue-400" /> :
                 <Sheet className="h-4 w-4 text-amber-400" />}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-bold text-white/70 truncate">{s.fuente_nombre}</p>
                <p className="text-[11px] text-white/30">{s.chunks} chunks · {s.fuente_tipo?.toUpperCase()} · {new Date(s.ultima_ingesta).toLocaleDateString()}</p>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] px-2 py-1 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-bold">
                  ✓ Procesado
                </span>
                <button onClick={() => handleDelete(s.fuente_nombre)} className="opacity-0 group-hover:opacity-100 p-1.5 text-white/20 hover:text-red-400 transition-all">
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// =============================================================================
// TAB 3: VALIDAR — Product catalog (rescued from /inventory)
// =============================================================================

function TabValidate() {
  const [products, setProducts] = useState<ProductData[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editPrecio, setEditPrecio] = useState(0);
  const [editStock, setEditStock] = useState(0);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        const data = await fetchProducts();
        setProducts(data);
      } catch { /* silent */ } finally { setLoading(false); }
    })();
  }, []);

  const filtered = products.filter(p =>
    p.nombre.toLowerCase().includes(search.toLowerCase()) ||
    (p.codigo && p.codigo.toLowerCase().includes(search.toLowerCase()))
  );

  const startEdit = (p: ProductData) => { setEditingId(p.id); setEditPrecio(p.precio); setEditStock(p.stock); };
  const cancelEdit = () => setEditingId(null);
  const saveEdit = async (id: string) => {
    setSaving(true);
    try {
      await updateProduct(id, { precio: editPrecio, stock: editStock });
      setProducts(prev => prev.map(p => p.id === id ? { ...p, precio: editPrecio, stock: editStock } : p));
      toast.success("Producto actualizado");
      setEditingId(null);
    } catch { toast.error("Error al actualizar"); } finally { setSaving(false); }
  };

  return (
    <div className="p-6 md:p-8 space-y-5 animate-in fade-in duration-300">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center">
            <Package className="h-5 w-5 text-amber-400" />
          </div>
          <div>
            <h2 className="text-lg font-black text-white">Catálogo Inteligente</h2>
            <p className="text-xs text-white/30">Productos y servicios que tu IA usa para vender</p>
          </div>
        </div>
        <span className="text-xs font-bold text-white/20">{products.length} productos</span>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-white/20" />
        <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Buscar por nombre o código..."
          className="w-full bg-white/5 border border-white/10 rounded-xl pl-11 pr-4 py-3 text-sm text-white placeholder:text-white/20 focus:outline-none focus:border-cyan-500/40" />
      </div>

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map(i => <div key={i} className="h-14 bg-white/[0.02] rounded-xl animate-pulse" />)}
        </div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-16">
          <Package className="h-10 w-10 text-white/10 mx-auto mb-3" />
          <p className="text-sm font-bold text-white/40">Sin productos detectados</p>
          <p className="text-xs text-white/20 mt-1">Sube un Excel o CSV en "Aprender" para extraer productos automáticamente.</p>
        </div>
      ) : (
        <div className="space-y-1.5">
          {/* Header */}
          <div className="grid grid-cols-12 gap-3 px-4 py-2 text-[10px] font-bold uppercase tracking-wider text-white/20">
            <span className="col-span-5">Producto</span>
            <span className="col-span-2">Estado</span>
            <span className="col-span-2 text-right">Precio</span>
            <span className="col-span-2 text-right">Stock</span>
            <span className="col-span-1"></span>
          </div>
          {filtered.map(p => {
            const isEditing = editingId === p.id;
            return (
              <div key={p.id} className="grid grid-cols-12 gap-3 items-center px-4 py-3 bg-white/[0.02] border border-white/5 rounded-xl hover:border-white/10 transition-colors">
                <div className="col-span-5">
                  <p className="text-sm font-bold text-white/70 truncate">{p.nombre}</p>
                  {p.codigo && <p className="text-[10px] text-white/20 font-mono">{p.codigo}</p>}
                </div>
                <div className="col-span-2">
                  <span className="text-[10px] px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-400/70 border border-emerald-500/20 font-bold">{p.estado}</span>
                </div>
                <div className="col-span-2 text-right">
                  {isEditing ? (
                    <input type="number" step="0.01" value={editPrecio} onChange={e => setEditPrecio(Number(e.target.value))}
                      className="w-20 ml-auto bg-white/5 border border-cyan-500/30 rounded-lg px-2 py-1 text-xs text-white text-right focus:outline-none" />
                  ) : (
                    <span className="text-sm font-bold text-white/60">${p.precio.toFixed(2)}</span>
                  )}
                </div>
                <div className="col-span-2 text-right">
                  {isEditing ? (
                    <input type="number" value={editStock} onChange={e => setEditStock(Number(e.target.value))}
                      className="w-16 ml-auto bg-white/5 border border-cyan-500/30 rounded-lg px-2 py-1 text-xs text-white text-right focus:outline-none" />
                  ) : (
                    <span className={`text-sm font-bold ${p.stock > 0 ? "text-white/60" : "text-red-400"}`}>{p.stock}</span>
                  )}
                </div>
                <div className="col-span-1 flex justify-end">
                  {isEditing ? (
                    <div className="flex gap-1">
                      <button onClick={() => saveEdit(p.id)} disabled={saving} className="p-1 text-cyan-400 hover:text-cyan-300">
                        {saving ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Save className="h-3.5 w-3.5" />}
                      </button>
                      <button onClick={cancelEdit} className="p-1 text-white/20 hover:text-white/50">
                        <X className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  ) : (
                    <button onClick={() => startEdit(p)} className="p-1 text-white/15 hover:text-white/40">
                      <Edit3 className="h-3.5 w-3.5" />
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// =============================================================================
// TAB 4: ASIGNAR — Agent ↔ Knowledge mapping
// =============================================================================

function TabAssign() {
  const [agents, setAgents] = useState<AgentResponse[]>([]);
  const [sources, setSources] = useState<KnowledgeSource[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        const [agentsData, knowledgeData] = await Promise.all([fetchAgents(), fetchKnowledge()]);
        setAgents(agentsData);
        setSources(knowledgeData.fuentes || []);
      } catch { /* silent */ } finally { setLoading(false); }
    })();
  }, []);

  return (
    <div className="p-6 md:p-8 space-y-5 animate-in fade-in duration-300">
      <div className="flex items-center gap-3 mb-2">
        <div className="h-10 w-10 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center">
          <Link2 className="h-5 w-5 text-purple-400" />
        </div>
        <div>
          <h2 className="text-lg font-black text-white">Asignación de Conocimiento</h2>
          <p className="text-xs text-white/30">Decide qué agente accede a qué información</p>
        </div>
      </div>

      {loading ? (
        <div className="space-y-3">
          {[1, 2].map(i => <div key={i} className="h-24 bg-white/[0.02] rounded-xl animate-pulse" />)}
        </div>
      ) : agents.length === 0 ? (
        <div className="text-center py-16">
          <Users2 className="h-10 w-10 text-white/10 mx-auto mb-3" />
          <p className="text-sm font-bold text-white/40">Sin agentes creados</p>
          <p className="text-xs text-white/20 mt-1">Crea tu primer agente en la sección "Agentes IA".</p>
        </div>
      ) : (
        <div className="space-y-3">
          {agents.map(agent => (
            <div key={agent.id} className="bg-white/[0.02] border border-white/5 rounded-xl p-5 hover:border-white/10 transition-colors">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="h-9 w-9 rounded-lg bg-cyan-500/10 flex items-center justify-center">
                    <Users2 className="h-4 w-4 text-cyan-400" />
                  </div>
                  <div>
                    <p className="text-sm font-bold text-white/70">{agent.nombre}</p>
                    <p className="text-[11px] text-white/30">{agent.agent_type} · {agent.modelo}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] px-2 py-1 rounded-lg bg-cyan-500/10 text-cyan-400/70 font-bold">
                    {agent.knowledge_base_size || 0} chunks
                  </span>
                  <span className={`text-[10px] px-2 py-1 rounded-lg font-bold ${
                    agent.estado === "activo" 
                      ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" 
                      : "bg-white/5 text-white/30"
                  }`}>
                    {agent.estado}
                  </span>
                </div>
              </div>

              {/* Knowledge sources assigned */}
              <div className="flex flex-wrap gap-2">
                {agent.coleccion_rag ? (
                  <span className="text-[11px] px-3 py-1.5 rounded-lg bg-purple-500/10 text-purple-400/70 border border-purple-500/20 font-medium flex items-center gap-1.5">
                    <Brain className="h-3 w-3" /> {agent.coleccion_rag}
                  </span>
                ) : sources.length > 0 ? (
                  <p className="text-[11px] text-white/20 italic">
                    Acceso al conocimiento global del tenant ({sources.reduce((s, f) => s + f.chunks, 0)} chunks disponibles)
                  </p>
                ) : (
                  <p className="text-[11px] text-white/20 italic">Sin conocimiento asignado</p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Info */}
      <div className="flex items-start gap-3 p-4 bg-cyan-500/5 border border-cyan-500/10 rounded-xl">
        <AlertCircle className="h-4 w-4 text-cyan-400/50 mt-0.5 flex-shrink-0" />
        <p className="text-xs text-white/30 leading-relaxed">
          Por defecto, todos los agentes acceden al conocimiento global del tenant.
          Para asignar colecciones RAG específicas, edita el agente desde la sección "Agentes IA" 
          y configura el campo <code className="bg-black/30 px-1 rounded text-[10px]">coleccion_rag</code>.
        </p>
      </div>
    </div>
  );
}
