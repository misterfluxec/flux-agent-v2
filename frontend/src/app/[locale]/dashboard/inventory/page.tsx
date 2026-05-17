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
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editPrecio, setEditPrecio] = useState<number>(0);
  const [editStock, setEditStock] = useState<number>(0);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    loadProducts();
  }, []);

  const loadProducts = async () => {
    try {
      setIsLoading(true);
      const data = await fetchProducts();
      setProducts(data);
    } catch (error) {
      toast.error("Error al cargar el inventario");
    } finally {
      setIsLoading(false);
    }
  };

  const filtered = products.filter(p => 
    p.name.toLowerCase().includes(search.toLowerCase()) || 
    (p.codigo && p.codigo.toLowerCase().includes(search.toLowerCase()))
  );

  const startEdit = (p: ProductData) => {
    setEditingId(p.id);
    setEditPrecio(p.price);
    setEditStock(p.stock);
  };

  const cancelEdit = () => {
    setEditingId(null);
  };

  const saveEdit = async (id: string) => {
    try {
      setIsSaving(true);
      await updateProduct(id, { price: editPrecio, stock: editStock });
      setProducts(prev => prev.map(p => p.id === id ? { ...p, price: editPrecio, stock: editStock } : p));
      toast.success("Producto actualizado");
      setEditingId(null);
    } catch (e) {
      toast.error("Error al actualizar");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="animate-entry max-w-5xl mx-auto space-y-6 pb-20">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 rounded-xl bg-primary/10 flex items-center justify-center border border-primary/20">
            <Package size={22} className="text-primary" />
          </div>
          <div>
            <h1 className="text-2xl font-extrabold text-foreground tracking-tight m-0">📦 Mi Inventario</h1>
            <p className="text-sm text-muted-foreground m-0">Gestiona los productos estructurados extraídos por la IA</p>
          </div>
        </div>
      </div>

      <Card className="bg-card border-border rounded-2xl overflow-hidden flux-card">
        <div className="p-4 border-b border-border flex gap-3">
          <div className="relative flex-1">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <Input 
              value={search} onChange={(e) => setSearch(e.target.value)} 
              placeholder="Buscar producto por name o código..." 
              className="pl-9 bg-input border-border rounded-lg" 
            />
          </div>
        </div>

        {isLoading ? (
          <div className="p-5 flex flex-col gap-3">
            {[1, 2, 3].map(i => <Skeleton key={i} className="h-12 w-full rounded-lg" />)}
          </div>
        ) : filtered.length === 0 ? (
          <div className="p-10 text-center">
            <Package size={40} className="mx-auto mb-3 text-muted-foreground opacity-50" />
            <p className="text-sm font-semibold text-foreground">No hay productos</p>
            <p className="text-[13px] text-muted-foreground">Sube un Excel o CSV en el Centro de Datos para extraer productos automáticamente.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader className="bg-secondary/50">
                <TableRow>
                  <TableHead className="text-[11px] font-bold text-muted-foreground uppercase">Nombre / Código</TableHead>
                  <TableHead className="text-[11px] font-bold text-muted-foreground uppercase">Estado</TableHead>
                  <TableHead className="text-[11px] font-bold text-muted-foreground uppercase">Precio</TableHead>
                  <TableHead className="text-[11px] font-bold text-muted-foreground uppercase">Stock</TableHead>
                  <TableHead className="w-20"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.map(p => {
                  const isEditing = editingId === p.id;
                  return (
                    <TableRow key={p.id} className="hover:bg-secondary/20 transition-colors duration-200">
                      <TableCell>
                        <p className="text-[13px] font-semibold text-foreground m-0">{p.name}</p>
                        {p.codigo && <p className="text-[11px] text-muted-foreground m-0 font-mono">{p.codigo}</p>}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className="bg-primary/10 text-primary border-primary/20 text-[10px] uppercase font-bold tracking-wider">{p.status}</Badge>
                      </TableCell>
                      <TableCell>
                        {isEditing ? (
                          <Input type="number" step="0.01" value={editPrecio} onChange={e => setEditPrecio(Number(e.target.value))} className="w-24 h-7 text-xs" />
                        ) : (
                          <span className="text-[13px] font-semibold tabular-nums">${p.price.toFixed(2)}</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {isEditing ? (
                          <Input type="number" value={editStock} onChange={e => setEditStock(Number(e.target.value))} className="w-20 h-7 text-xs" />
                        ) : (
                          <span className={`text-[13px] font-bold tabular-nums ${p.stock > 0 ? "text-foreground" : "text-destructive"}`}>
                            {p.stock}
                          </span>
                        )}
                      </TableCell>
                      <TableCell>
                        {isEditing ? (
                          <div className="flex gap-1">
                            <Button size="icon" variant="ghost" disabled={isSaving} onClick={() => saveEdit(p.id)} className="w-7 h-7 text-primary hover:bg-primary/10 cursor-pointer transition-all duration-200" aria-label="Guardar cambios">
                              {isSaving ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
                            </Button>
                            <Button size="icon" variant="ghost" disabled={isSaving} onClick={cancelEdit} className="w-7 h-7 text-muted-foreground hover:bg-destructive/10 hover:text-destructive cursor-pointer transition-all duration-200" aria-label="Cancelar edición">
                              <X size={14} />
                            </Button>
                          </div>
                        ) : (
                          <Button size="icon" variant="ghost" onClick={() => startEdit(p)} className="w-7 h-7 text-muted-foreground hover:bg-secondary cursor-pointer transition-all duration-200" aria-label="Editar producto">
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
