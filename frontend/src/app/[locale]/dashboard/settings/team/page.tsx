"use client";

import { useEffect, useState, useCallback } from "react";
import { 
  Users, Plus, Search, MoreVertical, Trash2, 
  Edit3, Shield, Eye, Bot, Mail, Clock, AlertCircle,
  CheckCircle, XCircle, UserPlus, Key
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";

interface TeamMember {
  id: string;
  email: string;
  nombre: string;
  rol: string;
  estado: string;
  ultimo_login: string | null;
  creado_en: string;
}

const ROLES = [
  { id: "admin", nombre: "Administrador", desc: "Acceso completo", icon: Shield },
  { id: "viewer", nombre: "Viewer", desc: "Solo lectura", icon: Eye },
  { id: "agente", nombre: "Agente", desc: "Operativo", icon: Bot },
];

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "https://api.labodegaec.com";

export default function EquipoPage() {
  const [miembros, setMiembros] = useState<TeamMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [editando, setEditando] = useState<TeamMember | null>(null);
  
  const [formNombre, setFormNombre] = useState("");
  const [formEmail, setFormEmail] = useState("");
  const [formRol, setFormRol] = useState("viewer");
  const [formPassword, setFormPassword] = useState("");
  const [saving, setSaving] = useState(false);

  const token = typeof window !== "undefined" ? localStorage.getItem("flux_token") : "";
  const userRol = typeof window !== "undefined" ? localStorage.getItem("flux_user_rol") : "admin";

  const loadMiembros = useCallback(async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/users`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setMiembros(data);
      }
    } catch (e) {
      console.error("Error loading members:", e);
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    loadMiembros();
  }, [loadMiembros]);

  const filteredMembers = miembros.filter(m => 
    m.nombre.toLowerCase().includes(search.toLowerCase()) ||
    m.email.toLowerCase().includes(search.toLowerCase())
  );

  const openNewModal = () => {
    setEditando(null);
    setFormNombre("");
    setFormEmail("");
    setFormRol("viewer");
    setFormPassword("");
    setModalOpen(true);
  };

  const openEditModal = (member: TeamMember) => {
    setEditando(member);
    setFormNombre(member.nombre);
    setFormEmail(member.email);
    setFormRol(member.rol);
    setFormPassword("");
    setModalOpen(true);
  };

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);

    try {
      const url = editando 
        ? `${BACKEND_URL}/api/v1/users/${editando.id}`
        : `${BACKEND_URL}/api/v1/users`;
      
      const method = editando ? "PATCH" : "POST";
      
      const body: any = {
        nombre: formNombre,
        rol: formRol,
      };
      
      if (editando) {
        if (formPassword) body.password = formPassword;
      } else {
        body.email = formEmail;
        if (formPassword) body.password = formPassword;
      }

      const res = await fetch(url, {
        method,
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(body),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Error al guardar");
      }

      toast.success(editando ? "Usuario actualizado" : "Usuario creado");
      setModalOpen(false);
      loadMiembros();
    } catch (e: any) {
      toast.error("Error", { description: e.message });
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(id: string) {
    if (!confirm("¿Estás seguro de eliminar este usuario?")) return;
    
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/users/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Error al eliminar");
      }
      
      toast.success("Usuario eliminado");
      loadMiembros();
    } catch (e: any) {
      toast.error("Error", { description: e.message });
    }
  }

  async function handleResetPassword(id: string) {
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/users/${id}/reset-password`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      
      if (!res.ok) throw new Error("Error al resetear");
      
      const data = await res.json();
      toast.success("Contraseña reseteada", { 
        description: `Nueva contraseña: ${data.password_temporal}` 
      });
    } catch (e: any) {
      toast.error("Error", { description: e.message });
    }
  }

  const getRoleBadge = (rol: string) => {
    const colors: Record<string, string> = {
      admin: "bg-purple-100 text-purple-700 border-purple-200",
      viewer: "bg-blue-100 text-blue-700 border-blue-200",
      agente: "bg-green-100 text-green-700 border-green-200",
    };
    const icons: Record<string, any> = {
      admin: Shield,
      viewer: Eye,
      agente: Bot,
    };
    const Icon = icons[rol] || Users;
    
    return (
      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs font-medium border ${colors[rol] || colors.viewer}`}>
        <Icon size={12} />
        {rol.charAt(0).toUpperCase() + rol.slice(1)}
      </span>
    );
  };

  const getStatusBadge = (estado: string) => {
    const configs: Record<string, { color: string; icon: any; label: string }> = {
      activo: { color: "text-green-600", icon: CheckCircle, label: "Activo" },
      inactivo: { color: "text-gray-500", icon: XCircle, label: "Inactivo" },
      suspended: { color: "text-red-600", icon: AlertCircle, label: "Suspendido" },
    };
    const config = configs[estado] || configs.inactivo;
    const Icon = config.icon;
    
    return (
      <span className={`inline-flex items-center gap-1 text-xs ${config.color}`}>
        <Icon size={12} />
        {config.label}
      </span>
    );
  };

  return (
    <div className="animate-entry max-w-5xl mx-auto pb-20">
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 24, flexWrap: "wrap", gap: 12 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{ width: 44, height: 44, borderRadius: 12, background: "var(--primary-light)", display: "flex", alignItems: "center", justifyContent: "center", border: "1px solid var(--primary-mid)" }}>
            <Users size={22} style={{ color: "var(--primary)" }} />
          </div>
          <div>
            <h1 style={{ fontSize: 24, fontWeight: 800, color: "var(--foreground)", margin: 0 }}>Mi Equipo</h1>
            <p style={{ fontSize: 14, color: "var(--muted-foreground)", margin: 0 }}>Gestiona los usuarios de tu organización</p>
          </div>
        </div>
        
        {userRol === "admin" && (
          <Button onClick={openNewModal} style={{ background: "var(--primary)", color: "white" }}>
            <Plus size={16} />
            <span style={{ marginLeft: 6 }}>Invitar usuario</span>
          </Button>
        )}
      </div>

      <Card style={{ padding: 0, background: "var(--card)", border: "1px solid var(--border)", borderRadius: "var(--radius)", overflow: "hidden" }}>
        <div style={{ padding: "16px 20px", borderBottom: "1px solid var(--border)", display: "flex", gap: 12 }}>
          <div style={{ position: "relative", flex: 1 }}>
            <Search size={16} style={{ position: "absolute", left: 12, top: "50%", transform: "translateY(-50%)", color: "var(--muted-foreground)" }} />
            <Input 
              value={search} onChange={(e) => setSearch(e.target.value)} 
              placeholder="Buscar por nombre o email..." 
              style={{ paddingLeft: 36, background: "var(--input)", borderRadius: 8 }} 
            />
          </div>
        </div>

        {loading ? (
          <div style={{ padding: 40, textAlign: "center" }}>
            <Users size={32} style={{ color: "var(--muted-foreground)", opacity: 0.5, margin: "0 auto 12px" }} />
            <p style={{ color: "var(--muted-foreground)" }}>Cargando equipo...</p>
          </div>
        ) : filteredMembers.length === 0 ? (
          <div style={{ padding: 40, textAlign: "center" }}>
            <Users size={40} style={{ color: "var(--muted-foreground)", opacity: 0.5, margin: "0 auto 12px" }} />
            <p style={{ fontSize: 14, fontWeight: 600, color: "var(--foreground)" }}>No hay usuarios</p>
            <p style={{ fontSize: 13, color: "var(--muted-foreground)" }}>Invita a tu primer miembro del equipo</p>
          </div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ background: "var(--secondary)" }}>
                  <th style={{ padding: "12px 20px", textAlign: "left", fontSize: 11, fontWeight: 600, color: "var(--muted-foreground)", textTransform: "uppercase" }}>Usuario</th>
                  <th style={{ padding: "12px 20px", textAlign: "left", fontSize: 11, fontWeight: 600, color: "var(--muted-foreground)", textTransform: "uppercase" }}>Rol</th>
                  <th style={{ padding: "12px 20px", textAlign: "left", fontSize: 11, fontWeight: 600, color: "var(--muted-foreground)", textTransform: "uppercase" }}>Estado</th>
                  <th style={{ padding: "12px 20px", textAlign: "left", fontSize: 11, fontWeight: 600, color: "var(--muted-foreground)", textTransform: "uppercase" }}>Último acceso</th>
                  <th style={{ padding: "12px 20px", textAlign: "right", fontSize: 11, fontWeight: 600, color: "var(--muted-foreground)", textTransform: "uppercase" }}>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {filteredMembers.map((member) => (
                  <tr key={member.id} style={{ borderBottom: "1px solid var(--border)" }}>
                    <td style={{ padding: "16px 20px" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                        <div style={{ 
                          width: 36, height: 36, borderRadius: "50%", 
                          background: "var(--primary-light)", 
                          display: "flex", alignItems: "center", justifyContent: "center",
                          fontSize: 14, fontWeight: 600, color: "var(--primary)"
                        }}>
                          {(member.nombre || member.email).charAt(0).toUpperCase()}
                        </div>
                        <div>
                          <p style={{ fontSize: 14, fontWeight: 600, color: "var(--foreground)", margin: 0 }}>{member.nombre || "Sin nombre"}</p>
                          <p style={{ fontSize: 12, color: "var(--muted-foreground)", margin: 0 }}>{member.email}</p>
                        </div>
                      </div>
                    </td>
                    <td style={{ padding: "16px 20px" }}>
                      {getRoleBadge(member.rol)}
                    </td>
                    <td style={{ padding: "16px 20px" }}>
                      {getStatusBadge(member.estado)}
                    </td>
                    <td style={{ padding: "16px 20px" }}>
                      {member.ultimo_login ? (
                        <span style={{ fontSize: 12, color: "var(--muted-foreground)", display: "flex", alignItems: "center", gap: 4 }}>
                          <Clock size={12} />
                          {new Date(member.ultimo_login).toLocaleDateString("es-EC", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" })}
                        </span>
                      ) : (
                        <span style={{ fontSize: 12, color: "var(--muted-foreground)" }}>Nunca</span>
                      )}
                    </td>
                    <td style={{ padding: "16px 20px", textAlign: "right" }}>
                      <div style={{ display: "flex", justifyContent: "flex-end", gap: 4 }}>
                        <Button 
                          size="icon" 
                          variant="ghost" 
                          onClick={() => handleResetPassword(member.id)}
                          title="Resetear contraseña"
                        >
                          <Key size={14} />
                        </Button>
                        <Button 
                          size="icon" 
                          variant="ghost" 
                          onClick={() => openEditModal(member)}
                          title="Editar"
                        >
                          <Edit3 size={14} />
                        </Button>
                        {userRol === "admin" && member.rol !== "admin" && (
                          <Button 
                            size="icon" 
                            variant="ghost" 
                            onClick={() => handleDelete(member.id)}
                            title="Eliminar"
                            className="text-destructive hover:text-destructive"
                          >
                            <Trash2 size={14} />
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {modalOpen && (
        <div style={{
          position: "fixed", inset: 0, zIndex: 50,
          background: "rgba(0,0,0,0.5)", display: "flex", alignItems: "center", justifyContent: "center",
          backdropFilter: "blur(4px)",
        }} onClick={() => setModalOpen(false)}>
          <div style={{
            background: "var(--card)", border: "1px solid var(--border)",
            borderRadius: "var(--radius)", padding: 24, width: "100%", maxWidth: 420,
            boxShadow: "var(--shadow-lg)",
          }} onClick={(e) => e.stopPropagation()}>
            <h2 style={{ fontSize: 18, fontWeight: 700, color: "var(--foreground)", margin: "0 0 20px" }}>
              {editando ? "Editar usuario" : "Invitar nuevo usuario"}
            </h2>
            
            <form onSubmit={handleSubmit}>
              {!editando && (
                <div style={{ marginBottom: 16 }}>
                  <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "var(--muted-foreground)", marginBottom: 6 }}>Email *</label>
                  <Input 
                    type="email" 
                    value={formEmail} onChange={(e) => setFormEmail(e.target.value)}
                    required
                    placeholder="usuario@empresa.com"
                    style={{ height: 40 }}
                  />
                </div>
              )}
              
              <div style={{ marginBottom: 16 }}>
                <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "var(--muted-foreground)", marginBottom: 6 }}>Nombre</label>
                <Input 
                  type="text" 
                  value={formNombre} onChange={(e) => setFormNombre(e.target.value)}
                  required
                  placeholder="Juan Pérez"
                  style={{ height: 40 }}
                />
              </div>
              
              <div style={{ marginBottom: 16 }}>
                <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "var(--muted-foreground)", marginBottom: 6 }}>Rol</label>
                <div style={{ display: "flex", gap: 8 }}>
                  {ROLES.map((rol) => (
                    <button
                      key={rol.id}
                      type="button"
                      onClick={() => setFormRol(rol.id)}
                      style={{
                        flex: 1,
                        padding: "10px 8px",
                        borderRadius: 8,
                        border: `2px solid ${formRol === rol.id ? "var(--primary)" : "var(--border)"}`,
                        background: formRol === rol.id ? "var(--primary-light)" : "transparent",
                        cursor: "pointer",
                        textAlign: "center",
                      }}
                    >
                      <rol.icon size={16} style={{ color: formRol === rol.id ? "var(--primary)" : "var(--muted-foreground)", marginBottom: 4 }} />
                      <p style={{ fontSize: 11, fontWeight: 600, color: "var(--foreground)", margin: 0 }}>{rol.nombre}</p>
                    </button>
                  ))}
                </div>
              </div>
              
              <div style={{ marginBottom: 20 }}>
                <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "var(--muted-foreground)", marginBottom: 6 }}>
                  {editando ? "Nueva contraseña (opcional)" : "Contraseña temporal"}
                </label>
                <Input 
                  type="password" 
                  value={formPassword} onChange={(e) => setFormPassword(e.target.value)}
                  placeholder={editando ? "Dejar vacío para mantener actual" : "Omitir para generar automáticamente"}
                  style={{ height: 40 }}
                />
              </div>
              
              <div style={{ display: "flex", gap: 12 }}>
                <Button 
                  type="button" 
                  variant="outline" 
                  onClick={() => setModalOpen(false)}
                  style={{ flex: 1 }}
                >
                  Cancelar
                </Button>
                <Button 
                  type="submit" 
                  disabled={saving}
                  style={{ flex: 1, background: "var(--primary)", color: "white" }}
                >
                  {saving ? "Guardando..." : (editando ? "Guardar cambios" : "Crear usuario")}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}