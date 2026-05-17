'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getCatalogItems, updateCatalogItem, CatalogItem, CatalogItemType } from '@/services/api/commerce';
import {
  ShoppingCart, Search, Edit3, Save, X, Loader2, Plus,
  Package, Wifi, Calendar, RefreshCw, Tag, LucideIcon
} from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import ProductFormModal from './components/ProductFormModal';
import PromotionsTab from './components/PromotionsTab';

// ─── TYPE BADGES ─────────────────────────────────────────────────────────
const TYPE_CONFIG: Record<CatalogItemType, { label: string; icon: LucideIcon; color: string }> = {
  physical_product: { label: 'Físico', icon: Package, color: 'bg-blue-500/10 text-blue-400 border-blue-500/20' },
  digital: { label: 'Digital', icon: Wifi, color: 'bg-purple-500/10 text-purple-400 border-purple-500/20' },
  service: { label: 'Servicio', icon: Tag, color: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' },
  booking: { label: 'Reserva', icon: Calendar, color: 'bg-amber-500/10 text-amber-400 border-amber-500/20' },
  subscription: { label: 'Suscripción', icon: RefreshCw, color: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20' },
};

export default function CatalogPage() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editPrice, setEditPrice] = useState(0);
  const [editStock, setEditStock] = useState(0);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<'items' | 'promotions'>('items');

  const { data: items = [], isLoading } = useQuery({
    queryKey: ['catalog'],
    queryFn: getCatalogItems,
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, updates }: { id: string; updates: { base_price?: number; stock_quantity?: number } }) =>
      updateCatalogItem(id, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['catalog'] });
      toast.success('Ítem actualizado correctamente');
      setEditingId(null);
    },
    onError: () => toast.error('Error al actualizar'),
  });

  const filtered = items.filter((item: CatalogItem) =>
    item.name.toLowerCase().includes(search.toLowerCase()) ||
    item.type.toLowerCase().includes(search.toLowerCase())
  );

  const startEdit = (item: CatalogItem) => {
    setEditingId(item.id);
    setEditPrice(item.base_price);
    setEditStock(item.stock_quantity);
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-500 pb-12 px-6 md:px-8 max-w-6xl mx-auto pt-6">
      
      <ProductFormModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} />

      {/* Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <ShoppingCart className="w-4 h-4 text-cyan-400" />
            <span className="text-[10px] font-bold uppercase tracking-widest text-cyan-400/80">Catálogo Unificado</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white/80">
            Catálogo Comercial
          </h1>
          <p className="text-sm text-white/40 mt-1">
            Productos, servicios, reservas y suscripciones — fuente de verdad única
          </p>
        </div>
        <Button 
          onClick={() => setIsModalOpen(true)}
          className="rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white h-11 px-6 font-bold shadow-[0_0_20px_rgba(6,182,212,0.2)]"
        >
          <Plus className="w-4 h-4 mr-2" /> Nuevo Ítem
        </Button>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" />
        <Input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Buscar por name o type..."
          className="pl-11 h-12 bg-white/[0.03] border-white/[0.06] rounded-xl text-white placeholder:text-white/20 focus:border-cyan-500/30"
        />
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {Object.entries(TYPE_CONFIG).map(([type, config]) => {
          const count = items.filter((i: CatalogItem) => i.type === type).length;
          const Icon = config.icon;
          return (
            <div key={type} className="bg-white/[0.02] border border-white/[0.05] rounded-xl p-3 flex items-center gap-3">
              <div className={`h-8 w-8 rounded-lg flex items-center justify-center border ${config.color}`}>
                <Icon className="w-3.5 h-3.5" />
              </div>
              <div>
                <p className="text-lg font-bold text-white/80">{count}</p>
                <p className="text-[10px] text-white/30 font-medium">{config.label}</p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-4 border-b border-white/5 pb-px">
        <button
          onClick={() => setActiveTab('items')}
          className={`pb-3 text-sm font-bold border-b-2 transition-all ${
            activeTab === 'items'
              ? 'border-cyan-500 text-cyan-400'
              : 'border-transparent text-white/40 hover:text-white/70'
          }`}
        >
          Inventario
        </button>
        <button
          onClick={() => setActiveTab('promotions')}
          className={`pb-3 text-sm font-bold border-b-2 transition-all ${
            activeTab === 'promotions'
              ? 'border-purple-500 text-purple-400'
              : 'border-transparent text-white/40 hover:text-white/70'
          }`}
        >
          Reglas y Promociones
        </button>
      </div>

      {/* Main Content */}
      {activeTab === 'items' ? (
        <div className="bg-[#111827] border border-white/5 rounded-2xl overflow-hidden shadow-lg">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
            <thead>
              <tr className="text-left border-b border-white/5">
                <th className="px-6 py-4 text-[11px] font-bold text-white/30 uppercase tracking-wider">Nombre</th>
                <th className="px-4 py-4 text-[11px] font-bold text-white/30 uppercase tracking-wider">Tipo</th>
                <th className="px-4 py-4 text-[11px] font-bold text-white/30 uppercase tracking-wider">Precio</th>
                <th className="px-4 py-4 text-[11px] font-bold text-white/30 uppercase tracking-wider">Stock</th>
                <th className="px-4 py-4 text-[11px] font-bold text-white/30 uppercase tracking-wider">Estado</th>
                <th className="px-4 py-4 w-24"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.03]">
              {isLoading ? (
                <tr><td colSpan={6} className="px-6 py-12 text-center text-white/30">
                  <Loader2 className="w-5 h-5 animate-spin mx-auto mb-2" />Cargando catálogo...
                </td></tr>
              ) : filtered.length === 0 ? (
                <tr><td colSpan={6} className="px-6 py-12 text-center">
                  <ShoppingCart className="w-8 h-8 text-white/10 mx-auto mb-3" />
                  <p className="text-sm font-semibold text-white/40">Sin ítems en el catálogo</p>
                  <p className="text-xs text-white/20 mt-1">Crea un nuevo ítem o importa desde CSV/Excel</p>
                </td></tr>
              ) : (
                filtered.map((item: CatalogItem) => {
                  const isEditing = editingId === item.id;
                  const typeConfig = TYPE_CONFIG[item.type] || TYPE_CONFIG.physical_product;
                  const TypeIcon = typeConfig.icon;
                  return (
                    <tr key={item.id} className="hover:bg-white/[0.02] transition-colors group">
                      <td className="px-6 py-4">
                        <p className="text-[13px] font-semibold text-white/80">{item.name}</p>
                        {item.description && (
                          <p className="text-[11px] text-white/30 mt-0.5 truncate max-w-xs">{item.description}</p>
                        )}
                      </td>
                      <td className="px-4 py-4">
                        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 text-[10px] font-bold rounded-lg border ${typeConfig.color}`}>
                          <TypeIcon className="w-3 h-3" />
                          {typeConfig.label}
                        </span>
                      </td>
                      <td className="px-4 py-4">
                        {isEditing ? (
                          <Input
                            type="number" step="0.01" value={editPrice}
                            onChange={e => setEditPrice(Number(e.target.value))}
                            className="w-24 h-8 text-xs bg-white/5 border-white/10 rounded-lg"
                          />
                        ) : (
                          <span className="text-[13px] font-bold text-white/80 tabular-nums">
                            ${item.base_price.toFixed(2)}
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-4">
                        {isEditing ? (
                          <Input
                            type="number" value={editStock}
                            onChange={e => setEditStock(Number(e.target.value))}
                            className="w-20 h-8 text-xs bg-white/5 border-white/10 rounded-lg"
                          />
                        ) : (
                          <span className={`text-[13px] font-bold tabular-nums ${item.stock_quantity > 0 ? 'text-white/80' : 'text-red-400'}`}>
                            {item.stock_quantity}
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-4">
                        <Badge variant="outline" className={`text-[10px] ${
                          item.status === 'active' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' :
                          'bg-white/5 text-white/40 border-white/10'
                        }`}>
                          {item.status === 'active' ? 'Activo' : item.status}
                        </Badge>
                      </td>
                      <td className="px-4 py-4">
                        {isEditing ? (
                          <div className="flex gap-1">
                            <Button size="icon" variant="ghost" className="h-8 w-8 text-cyan-400 hover:text-cyan-300"
                              disabled={updateMutation.isPending}
                              onClick={() => updateMutation.mutate({ id: item.id, updates: { base_price: editPrice, stock_quantity: editStock } })}>
                              {updateMutation.isPending ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
                            </Button>
                            <Button size="icon" variant="ghost" className="h-8 w-8 text-white/30 hover:text-white/50"
                              onClick={() => setEditingId(null)}>
                              <X className="w-3.5 h-3.5" />
                            </Button>
                          </div>
                        ) : (
                          <Button size="icon" variant="ghost"
                            className="h-8 w-8 text-white/20 opacity-0 group-hover:opacity-100 hover:text-white/50 transition-all"
                            onClick={() => startEdit(item)}>
                            <Edit3 className="w-3.5 h-3.5" />
                          </Button>
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
      ) : (
        <PromotionsTab />
      )}
    </div>
  );
}
