'use client';

import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { X, Package, Tag, Clock, Save, Loader2, Info } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { api as apiClient } from '@/services/api/client';
import { toast } from 'sonner';
import { CatalogItemType } from '@/services/api/commerce';

interface ProductFormModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function ProductFormModal({ isOpen, onClose }: ProductFormModalProps) {
  const queryClient = useQueryClient();
  
  // State
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [basePrice, setBasePrice] = useState(0);
  const [productType, setProductType] = useState<CatalogItemType>('physical_product');
  
  // Capabilities State
  const [capabilities, setCapabilities] = useState({
    requires_inventory: true,
    requires_shipping: true,
    requires_appointment: false,
    stock_quantity: 0,
    duration_minutes: 30,
  });

  // Preset Logic (React to Product Type changes)
  const handleTypeChange = (newType: CatalogItemType) => {
    setProductType(newType);
    if (newType === 'service' || newType === 'booking') {
      setCapabilities(prev => ({ ...prev, requires_appointment: true, requires_inventory: false, requires_shipping: false }));
    } else if (newType === 'physical_product') {
      setCapabilities(prev => ({ ...prev, requires_inventory: true, requires_shipping: true, requires_appointment: false }));
    } else if (newType === 'digital' || newType === 'subscription') {
      setCapabilities(prev => ({ ...prev, requires_inventory: false, requires_shipping: false, requires_appointment: false }));
    }
  };

  const createMutation = useMutation({
    mutationFn: async (payload: Record<string, unknown>) => {
      // In a real app we'd add POST /api/v1/catalog endpoint directly, 
      // but for now we use /import bulk endpoint since we updated it
      const response = await apiClient.post<any>('/catalog/import', {
        items: [payload]
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['catalog'] });
      toast.success('Producto creado exitosamente');
      onClose();
      // Reset
      setName('');
      setDescription('');
      setBasePrice(0);
    },
    onError: () => toast.error('Error al crear el producto')
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || basePrice < 0) return;

    createMutation.mutate({
      name,
      description,
      type: productType,
      base_price: basePrice,
      capabilities: {
        requires_inventory: capabilities.requires_inventory,
        requires_shipping: capabilities.requires_shipping,
        requires_appointment: capabilities.requires_appointment,
        stock_quantity: capabilities.requires_inventory ? Number(capabilities.stock_quantity) : null,
        duration_minutes: capabilities.requires_appointment ? Number(capabilities.duration_minutes) : null,
      }
    });
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in">
      <div className="bg-gray-950 border border-white/10 rounded-2xl w-full max-w-2xl overflow-hidden shadow-2xl flex flex-col max-h-[90vh]">
        
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-white/5">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-cyan-500/10 flex items-center justify-center border border-cyan-500/20">
              <Package className="w-5 h-5 text-cyan-400" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white/90">Nuevo Ítem</h2>
              <p className="text-xs text-white/40">Configura capacidades del producto</p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-white/5 rounded-lg transition-colors">
            <X className="w-5 h-5 text-white/40" />
          </button>
        </div>

        {/* Form Body */}
        <div className="flex-1 overflow-y-auto p-6">
          <form id="product-form" onSubmit={handleSubmit} className="space-y-8">
            
            {/* General Info */}
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-bold text-white/50 uppercase tracking-widest mb-2 block">Nombre</label>
                  <Input 
                    value={name} onChange={e => setName(e.target.value)}
                    placeholder="Silla Gamer Pro"
                    className="bg-white/5 border-white/10 text-white"
                    required
                  />
                </div>
                <div>
                  <label className="text-xs font-bold text-white/50 uppercase tracking-widest mb-2 block">Precio Base</label>
                  <Input 
                    type="number" step="0.01" min="0"
                    value={basePrice} onChange={e => setBasePrice(Number(e.target.value))}
                    className="bg-white/5 border-white/10 text-white"
                    required
                  />
                </div>
              </div>
              <div>
                <label className="text-xs font-bold text-white/50 uppercase tracking-widest mb-2 block">Descripción</label>
                <textarea 
                  value={description} onChange={e => setDescription(e.target.value)}
                  className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-sm text-white focus:outline-none focus:border-cyan-500/50 min-h-[80px]"
                />
              </div>
            </div>

            {/* Type Preset */}
            <div>
              <label className="text-xs font-bold text-white/50 uppercase tracking-widest mb-3 block">Naturaleza del Producto</label>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {[
                  { id: 'physical_product', label: 'Físico', icon: Package },
                  { id: 'service', label: 'Servicio', icon: Tag },
                  { id: 'digital', label: 'Digital', icon: Info },
                  { id: 'subscription', label: 'Suscripción', icon: Clock },
                ].map(t => (
                  <button
                    key={t.id} type="button"
                    onClick={() => handleTypeChange(t.id as CatalogItemType)}
                    className={`flex flex-col items-center justify-center gap-2 p-3 rounded-xl border transition-all ${
                      productType === t.id 
                        ? 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400' 
                        : 'bg-white/5 border-white/10 text-white/50 hover:bg-white/10'
                    }`}
                  >
                    <t.icon className="w-5 h-5" />
                    <span className="text-xs font-semibold">{t.label}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Capabilities Toggles (The "Brain") */}
            <div className="bg-white/[0.02] border border-white/5 rounded-xl p-5 space-y-4">
              <h3 className="text-sm font-bold text-white/80 border-b border-white/10 pb-2">Capacidades del Sistema</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
                
                {/* Requires Inventory */}
                <div className="space-y-3">
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input 
                      type="checkbox" 
                      className="w-4 h-4 rounded border-white/20 bg-black/50 text-cyan-500 focus:ring-cyan-500/50"
                      checked={capabilities.requires_inventory}
                      onChange={e => setCapabilities(p => ({ ...p, requires_inventory: e.target.checked }))}
                    />
                    <span className="text-sm font-medium text-white/80">Gestionar Stock</span>
                  </label>
                  {capabilities.requires_inventory && (
                    <div className="pl-7 animate-in slide-in-from-top-2">
                      <Input 
                        type="number" min="0" placeholder="Stock Inicial"
                        value={capabilities.stock_quantity}
                        onChange={e => setCapabilities(p => ({ ...p, stock_quantity: Number(e.target.value) }))}
                        className="bg-white/5 border-white/10 h-8 text-xs"
                      />
                    </div>
                  )}
                </div>

                {/* Requires Shipping */}
                <div>
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input 
                      type="checkbox" 
                      className="w-4 h-4 rounded border-white/20 bg-black/50 text-cyan-500 focus:ring-cyan-500/50"
                      checked={capabilities.requires_shipping}
                      onChange={e => setCapabilities(p => ({ ...p, requires_shipping: e.target.checked }))}
                    />
                    <span className="text-sm font-medium text-white/80">Requiere Envío (Logística)</span>
                  </label>
                </div>

                {/* Requires Appointment */}
                <div className="space-y-3 md:col-span-2 pt-2 border-t border-white/5">
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input 
                      type="checkbox" 
                      className="w-4 h-4 rounded border-white/20 bg-black/50 text-cyan-500 focus:ring-cyan-500/50"
                      checked={capabilities.requires_appointment}
                      onChange={e => setCapabilities(p => ({ ...p, requires_appointment: e.target.checked }))}
                    />
                    <span className="text-sm font-medium text-white/80">Requiere Agendar Cita (Booking)</span>
                  </label>
                  {capabilities.requires_appointment && (
                    <div className="pl-7 animate-in slide-in-from-top-2 grid grid-cols-2 gap-4">
                      <div>
                        <label className="text-[10px] text-white/40 mb-1 block">Duración (min)</label>
                        <Input 
                          type="number" min="15" step="15"
                          value={capabilities.duration_minutes}
                          onChange={e => setCapabilities(p => ({ ...p, duration_minutes: Number(e.target.value) }))}
                          className="bg-white/5 border-white/10 h-8 text-xs"
                        />
                      </div>
                    </div>
                  )}
                </div>

              </div>
            </div>

          </form>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-white/5 bg-white/[0.02] flex justify-end gap-3">
          <Button type="button" variant="ghost" onClick={onClose} className="text-white/50 hover:text-white">
            Cancelar
          </Button>
          <Button type="submit" form="product-form" disabled={createMutation.isPending} className="bg-cyan-600 hover:bg-cyan-500 text-white px-6">
            {createMutation.isPending ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Save className="w-4 h-4 mr-2" />}
            Guardar Ítem
          </Button>
        </div>

      </div>
    </div>
  );
}
