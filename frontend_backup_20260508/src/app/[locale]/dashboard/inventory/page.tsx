"use client";

import { useEffect, useState } from "react";
import { fetchProducts, updateProduct, ProductData } from "@/lib/api";
import { Package, Search, Edit3, Save, X, Loader2 } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";

export default function InventarioPage() {
  const [products, setProducts] = useState<ProductData[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editPrecio, setEditPrecio] = useState<number>(0);
  const [editStock, setEditStock] = useState<number>(0);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadProducts();
  }, []);

  const loadProducts = async () => {
    try {
      setLoading(true);
      const data = await fetchProducts();
      setProducts(data);
    } catch (error) {
      toast.error("Error al cargar el inventario");
    } finally {
      setLoading(false);
    }
  };

  const filtered = products.filter(p => 
    p.nombre.toLowerCase().includes(search.toLowerCase()) || 
    (p.codigo && p.codigo.toLowerCase().includes(search.toLowerCase()))
  );

  const startEdit = (p: ProductData) => {
    setEditingId(p.id);
    setEditPrecio(p.precio);
    setEditStock(p.stock);
  };

  const cancelEdit = () => {
    setEditingId(null);
  };

  const saveEdit = async (id: string) => {
    try {
      setSaving(true);
      await updateProduct(id, { precio: editPrecio, stock: editStock });
      setProducts(prev => prev.map(p => p.id === id ? { ...p, precio: editPrecio, stock: editStock } : p));
      toast.success("Producto actualizado");
      setEditingId(null);
    } catch (e) {
      toast.error("Error al actualizar");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="animate-entry max-w-5xl mx-auto space-y-6 pb-20">
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 12 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{ width: 44, height: 44, borderRadius: "var(--radius)", background: "var(--primary-light)", display: "flex", alignItems: "center", justifyContent: "center", border: "1px solid var(--primary-mid)" }}>
            <Package size={22} style={{ color: "var(--primary)" }} />
          </div>
          <div>
            <h1 style={{ fontSize: 24, fontWeight: 800, color: "var(--foreground)", margin: 0 }}>📦 Mi Inventario</h1>
            <p style={{ fontSize: 14, color: "var(--muted-foreground)", margin: 0 }}>Gestiona los productos estructurados extraídos por la IA</p>
          </div>
        </div>
      </div>

      <Card style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: "var(--radius)", overflow: "hidden" }}>
        <div style={{ padding: "16px 20px", borderBottom: "1px solid var(--border)", display: "flex", gap: 10 }}>
          <div style={{ position: "relative", flex: 1 }}>
            <Search size={16} style={{ position: "absolute", left: 12, top: "50%", transform: "translateY(-50%)", color: "var(--muted-foreground)" }} />
            <Input 
              value={search} onChange={(e) => setSearch(e.target.value)} 
              placeholder="Buscar producto por nombre o código..." 
              style={{ paddingLeft: 36, background: "var(--input)", border: "1px solid var(--border)", borderRadius: 8 }} 
            />
          </div>
        </div>

        {loading ? (
          <div style={{ padding: 20, display: "flex", flexDirection: "column", gap: 10 }}>
            {[1, 2, 3].map(i => <Skeleton key={i} className="h-12 w-full" style={{ borderRadius: 8 }} />)}
          </div>
        ) : filtered.length === 0 ? (
          <div style={{ padding: 40, textAlign: "center" }}>
            <Package size={40} style={{ margin: "0 auto 12px", color: "var(--muted-foreground)", opacity: 0.5 }} />
            <p style={{ fontSize: 14, fontWeight: 600, color: "var(--foreground)" }}>No hay productos</p>
            <p style={{ fontSize: 13, color: "var(--muted-foreground)" }}>Sube un Excel o CSV en el Centro de Datos para extraer productos automáticamente.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader style={{ background: "var(--secondary)" }}>
                <TableRow>
                  <TableHead style={{ fontSize: 11, fontWeight: 700, color: "var(--muted-foreground)", textTransform: "uppercase" }}>Nombre / Código</TableHead>
                  <TableHead style={{ fontSize: 11, fontWeight: 700, color: "var(--muted-foreground)", textTransform: "uppercase" }}>Estado</TableHead>
                  <TableHead style={{ fontSize: 11, fontWeight: 700, color: "var(--muted-foreground)", textTransform: "uppercase" }}>Precio</TableHead>
                  <TableHead style={{ fontSize: 11, fontWeight: 700, color: "var(--muted-foreground)", textTransform: "uppercase" }}>Stock</TableHead>
                  <TableHead style={{ width: 80 }}></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.map(p => {
                  const isEditing = editingId === p.id;
                  return (
                    <TableRow key={p.id}>
                      <TableCell>
                        <p style={{ fontSize: 13, fontWeight: 600, color: "var(--foreground)", margin: 0 }}>{p.nombre}</p>
                        {p.codigo && <p style={{ fontSize: 11, color: "var(--muted-foreground)", margin: 0, fontFamily: "monospace" }}>{p.codigo}</p>}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" style={{ background: "var(--primary-light)", color: "var(--primary)", border: "1px solid var(--primary-mid)", fontSize: 10 }}>{p.estado}</Badge>
                      </TableCell>
                      <TableCell>
                        {isEditing ? (
                          <Input type="number" step="0.01" value={editPrecio} onChange={e => setEditPrecio(Number(e.target.value))} style={{ width: 90, height: 28, fontSize: 12 }} />
                        ) : (
                          <span style={{ fontSize: 13, fontWeight: 600 }}>${p.precio.toFixed(2)}</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {isEditing ? (
                          <Input type="number" value={editStock} onChange={e => setEditStock(Number(e.target.value))} style={{ width: 80, height: 28, fontSize: 12 }} />
                        ) : (
                          <span style={{ fontSize: 13, fontWeight: 600, color: p.stock > 0 ? "var(--foreground)" : "var(--destructive)" }}>
                            {p.stock}
                          </span>
                        )}
                      </TableCell>
                      <TableCell>
                        {isEditing ? (
                          <div style={{ display: "flex", gap: 4 }}>
                            <Button size="icon" variant="ghost" disabled={saving} onClick={() => saveEdit(p.id)} style={{ width: 28, height: 28, color: "var(--primary)" }}>
                              {saving ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
                            </Button>
                            <Button size="icon" variant="ghost" disabled={saving} onClick={cancelEdit} style={{ width: 28, height: 28, color: "var(--muted-foreground)" }}>
                              <X size={14} />
                            </Button>
                          </div>
                        ) : (
                          <Button size="icon" variant="ghost" onClick={() => startEdit(p)} style={{ width: 28, height: 28, color: "var(--muted-foreground)" }}>
                            <Edit3 size={14} />
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
        )}
      </Card>
    </div>
  );
}
