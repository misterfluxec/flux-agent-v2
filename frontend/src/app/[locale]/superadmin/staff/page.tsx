"use client";

import { useState } from "react";
import {
  Users, Plus, Shield, Eye, Headphones, Search,
  Trash2, Edit3, Key, CheckCircle, XCircle, X
} from "lucide-react";
import { toast } from "sonner";

interface StaffMember {
  id: string;
  name: string;
  email: string;
  role: string;
  status: string;
  last_login: string;
}

const ROLES = [
  { id: "super_admin",  label: "Super Admin",    desc: "Acceso total al sistema",     icon: Shield,     color: "text-purple-400 bg-purple-500/10 border-purple-500/20" },
  { id: "soporte",      label: "Soporte NOC",     desc: "Gestión de tickets y logs",   icon: Headphones, color: "text-blue-400   bg-blue-500/10   border-blue-500/20" },
  { id: "facturacion",  label: "Facturación",     desc: "Solo módulo de pagos",        icon: Key,        color: "text-amber-400  bg-amber-500/10  border-amber-500/20" },
  { id: "viewer",       label: "Viewer",          desc: "Solo lectura",                icon: Eye,        color: "text-slate-400  bg-slate-500/10  border-slate-500/20" },
];

const INITIAL_MEMBERS: StaffMember[] = [
  { id: "1", name: "Admin Principal", email: "admin@fluxagent.com",   role: "super_admin", status: "is_active", last_login: "2026-04-30T10:30:00Z" },
  { id: "2", name: "Soporte Técnico", email: "soporte@fluxagent.com", role: "soporte",     status: "is_active", last_login: "2026-04-29T15:45:00Z" },
  { id: "3", name: "Contabilidad",    email: "contable@fluxagent.com",role: "facturacion", status: "is_active", last_login: "2026-04-28T09:00:00Z" },
];

function RoleBadge({ role }: { role: string }) {
  const cfg = ROLES.find(r => r.id === role) || ROLES[3];
  const Icon = cfg.icon;
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium border ${cfg.color}`}>
      <Icon size={11} />
      {cfg.label}
    </span>
  );
}

export default function StaffPage() {
  const [members,    setMembers]    = useState<StaffMember[]>(INITIAL_MEMBERS);
  const [search,     setSearch]     = useState("");
  const [modalOpen,  setModalOpen]  = useState(false);
  const [formNombre, setFormNombre] = useState("");
  const [formEmail,  setFormEmail]  = useState("");
  const [formRol,    setFormRol]    = useState("viewer");

  const filtered = members.filter(m =>
    m.name.toLowerCase().includes(search.toLowerCase()) ||
    m.email.toLowerCase().includes(search.toLowerCase())
  );

  const handleCreate = () => {
    if (!formNombre || !formEmail) { toast.error("Completa todos los campos"); return; }
    setMembers(prev => [...prev, {
      id: Date.now().toString(), name: formNombre, email: formEmail,
      role: formRol, status: "is_active", last_login: new Date().toISOString(),
    }]);
    toast.success(`Usuario ${formNombre} creado`);
    setModalOpen(false); setFormNombre(""); setFormEmail(""); setFormRol("viewer");
  };

  return (
    <div className="space-y-8 animate-entry pb-20">
      {/* Cabecera */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Staff del Sistema</h1>
          <p className="text-slate-500 text-sm mt-1">Gestión de users internos del NOC y sus permisos</p>
        </div>
        <button
          onClick={() => setModalOpen(true)}
          className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2.5 rounded-xl text-sm font-semibold transition-all shadow-lg shadow-emerald-600/20"
        >
          <Plus className="w-4 h-4" />
          Nuevo Administrador
        </button>
      </div>

      {/* Contadores por Rol */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {ROLES.map(role => {
          const count = members.filter(m => m.role === role.id).length;
          const Icon  = role.icon;
          return (
            <div key={role.id} className="bg-slate-900 border border-slate-800 p-5 rounded-2xl">
              <div className={`w-9 h-9 rounded-xl flex items-center justify-center border mb-3 ${role.color}`}>
                <Icon size={16} />
              </div>
              <div className="text-2xl font-bold text-slate-100">{count}</div>
              <div className="text-xs text-slate-500 mt-0.5">{role.label}</div>
            </div>
          );
        })}
      </div>

      {/* Tabla */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl">
        <div className="p-4 border-b border-slate-800 flex gap-3">
          <div className="relative flex-1 max-w-xs">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 pointer-events-none" />
            <input
              value={search} onChange={e => setSearch(e.target.value)}
              placeholder="Buscar administrador..."
              className="w-full bg-slate-950 border border-slate-800 rounded-lg py-2 pl-9 pr-4 text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-emerald-500/50"
            />
          </div>
        </div>
        <table className="w-full text-left">
          <thead className="bg-slate-950/60 text-[10px] uppercase tracking-widest text-slate-500 font-bold">
            <tr>
              <th className="px-6 py-4">Usuario</th>
              <th className="px-6 py-4">Rol</th>
              <th className="px-6 py-4">Estado</th>
              <th className="px-6 py-4">Último Acceso</th>
              <th className="px-6 py-4 text-right">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {filtered.map(m => (
              <tr key={m.id} className="hover:bg-slate-800/30 transition-colors">
                <td className="px-6 py-4">
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center text-sm font-bold text-emerald-400">
                      {m.name.charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <div className="text-sm font-semibold text-slate-200">{m.name}</div>
                      <div className="text-xs text-slate-500">{m.email}</div>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4"><RoleBadge role={m.role} /></td>
                <td className="px-6 py-4">
                  {m.status === "is_active" ? (
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium bg-emerald-500/10 text-emerald-400">
                      <CheckCircle size={11} /> Activo
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium bg-red-500/10 text-red-400">
                      <XCircle size={11} /> Inactivo
                    </span>
                  )}
                </td>
                <td className="px-6 py-4 text-xs text-slate-400">
                  {new Date(m.last_login).toLocaleString("es-EC", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" })}
                </td>
                <td className="px-6 py-4 text-right">
                  <div className="flex justify-end gap-1">
                    <button onClick={() => toast.info("Editar: " + m.name)}
                      className="p-2 hover:bg-slate-700 rounded-lg text-slate-400 transition-colors" title="Editar">
                      <Edit3 size={14} />
                    </button>
                    <button onClick={() => toast.info("Cambiar role: " + m.name)}
                      className="p-2 hover:bg-slate-700 rounded-lg text-slate-400 transition-colors" title="Cambiar role">
                      <Key size={14} />
                    </button>
                    <button onClick={() => { setMembers(prev => prev.filter(x => x.id !== m.id)); toast.success("Usuario eliminado"); }}
                      className="p-2 hover:bg-red-500/10 rounded-lg text-slate-500 hover:text-red-400 transition-colors" title="Eliminar">
                      <Trash2 size={14} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Modal Nuevo Administrador */}
      {modalOpen && (
        <div
          className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4"
          onClick={() => setModalOpen(false)}
        >
          <div
            className="bg-slate-900 border border-slate-700 rounded-2xl p-6 w-full max-w-md shadow-2xl"
            onClick={e => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-bold text-slate-100">Nuevo Administrador</h2>
              <button onClick={() => setModalOpen(false)} className="p-1.5 hover:bg-slate-800 rounded-lg text-slate-400">
                <X size={16} />
              </button>
            </div>

            <div className="space-y-4 mb-6">
              <div>
                <label className="text-xs font-semibold text-slate-400 block mb-1.5">Nombre completo</label>
                <input value={formNombre} onChange={e => setFormNombre(e.target.value)} placeholder="Juan Pérez"
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg py-2.5 px-3 text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-emerald-500/50"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-400 block mb-1.5">Email corporativo</label>
                <input value={formEmail} onChange={e => setFormEmail(e.target.value)} placeholder="name@fluxagent.com" type="email"
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg py-2.5 px-3 text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-emerald-500/50"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-400 block mb-2">Nivel de acceso</label>
                <div className="space-y-2">
                  {ROLES.map(role => {
                    const Icon = role.icon;
                    return (
                      <button key={role.id} onClick={() => setFormRol(role.id)} type="button"
                        className={`w-full flex items-center gap-3 p-3 rounded-xl border text-left transition-all ${
                          formRol === role.id
                            ? "border-emerald-500/40 bg-emerald-500/5"
                            : "border-slate-800 hover:border-slate-700"
                        }`}
                      >
                        <Icon size={16} className={formRol === role.id ? "text-emerald-400" : "text-slate-500"} />
                        <div>
                          <p className="text-sm font-semibold text-slate-200">{role.label}</p>
                          <p className="text-xs text-slate-500">{role.desc}</p>
                        </div>
                        {formRol === role.id && <CheckCircle size={14} className="text-emerald-400 ml-auto" />}
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>

            <div className="flex gap-3">
              <button onClick={() => setModalOpen(false)}
                className="flex-1 border border-slate-700 text-slate-300 hover:text-slate-100 hover:border-slate-600 py-2.5 rounded-xl text-sm font-medium transition-all">
                Cancelar
              </button>
              <button onClick={handleCreate}
                className="flex-1 bg-emerald-600 hover:bg-emerald-500 text-white py-2.5 rounded-xl text-sm font-semibold transition-all shadow-lg shadow-emerald-600/20">
                Crear Usuario
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}