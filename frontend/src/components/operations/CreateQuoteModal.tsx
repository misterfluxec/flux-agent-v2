import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createQuote } from '@/services/api/commerce';
import { toast } from 'sonner';
import { X, Loader2, Plus, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';

export function CreateQuoteModal({ 
  isOpen, 
  onClose, 
  customerId,
  customerName
}: { 
  isOpen: boolean; 
  onClose: () => void; 
  customerId: string;
  customerName?: string;
}) {
  const queryClient = useQueryClient();
  const [items, setItems] = useState([{ catalog_item_id: '', description: '', quantity: 1, unit_price: 0 }]);
  
  const mutation = useMutation({
    mutationFn: () => {
      // Calculate total
      const total = items.reduce((sum, item) => sum + (item.quantity * item.unit_price), 0);
      return createQuote({ customer_id: customerId, items });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['quotes'] });
      toast.success('Cotización generada correctamente');
      onClose();
    },
    onError: (err: any) => {
      toast.error('Error al generar cotización: ' + (err.message || 'Error desconocido'));
    }
  });

  if (!isOpen) return null;

  const addItem = () => setItems([...items, { catalog_item_id: '', description: '', quantity: 1, unit_price: 0 }]);
  const removeItem = (index: number) => setItems(items.filter((_, i) => i !== index));
  const updateItem = (index: number, field: string, value: any) => {
    const newItems = [...items];
    (newItems[index] as any)[field] = value;
    setItems(newItems);
  };

  const total = items.reduce((sum, item) => sum + (item.quantity * item.unit_price), 0);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-slate-900 border border-white/10 w-full max-w-lg rounded-2xl shadow-2xl animate-in zoom-in-95 overflow-hidden flex flex-col max-h-[90vh]">
        
        <div className="flex items-center justify-between p-6 border-b border-white/5 bg-slate-900">
          <div>
            <h2 className="text-lg font-bold text-white">Generar Cotización</h2>
            <p className="text-xs text-slate-400 mt-1">Para: {customerName || customerId}</p>
          </div>
          <button onClick={onClose} className="p-2 text-slate-400 hover:text-white rounded-lg hover:bg-white/5 transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 overflow-y-auto space-y-4">
          {items.map((item, index) => (
            <div key={index} className="flex flex-wrap gap-2 items-end p-3 bg-white/5 rounded-lg border border-white/5">
              <div className="flex-1 min-w-[120px]">
                <label className="text-[10px] uppercase font-bold text-slate-400 mb-1 block">Descripción</label>
                <input 
                  type="text" 
                  value={item.description}
                  onChange={(e) => updateItem(index, 'description', e.target.value)}
                  className="w-full bg-slate-950 border border-white/10 rounded px-3 py-2 text-sm text-white"
                  placeholder="Ej. Plan Pro Mensual"
                />
              </div>
              <div className="w-20">
                <label className="text-[10px] uppercase font-bold text-slate-400 mb-1 block">ID Ítem</label>
                <input 
                  type="text" 
                  value={item.catalog_item_id}
                  onChange={(e) => updateItem(index, 'catalog_item_id', e.target.value)}
                  className="w-full bg-slate-950 border border-white/10 rounded px-3 py-2 text-sm text-white"
                  placeholder="ID"
                />
              </div>
              <div className="w-16">
                <label className="text-[10px] uppercase font-bold text-slate-400 mb-1 block">Cant</label>
                <input 
                  type="number" 
                  min="1"
                  value={item.quantity}
                  onChange={(e) => updateItem(index, 'quantity', parseInt(e.target.value))}
                  className="w-full bg-slate-950 border border-white/10 rounded px-3 py-2 text-sm text-white"
                />
              </div>
              <div className="w-24">
                <label className="text-[10px] uppercase font-bold text-slate-400 mb-1 block">Precio ($)</label>
                <input 
                  type="number" 
                  min="0"
                  step="0.01"
                  value={item.unit_price}
                  onChange={(e) => updateItem(index, 'unit_price', parseFloat(e.target.value))}
                  className="w-full bg-slate-950 border border-white/10 rounded px-3 py-2 text-sm text-white"
                />
              </div>
              <button 
                onClick={() => removeItem(index)}
                className="p-2 text-red-400 hover:bg-red-500/20 rounded"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}

          <button 
            onClick={addItem}
            className="flex items-center text-xs font-bold text-cyan-400 hover:text-cyan-300 transition-colors"
          >
            <Plus className="w-4 h-4 mr-1" />
            Agregar Ítem
          </button>
        </div>

        <div className="p-6 border-t border-white/5 bg-slate-950 flex items-center justify-between">
          <div>
            <span className="text-xs text-slate-400">Total:</span>
            <span className="ml-2 text-lg font-bold text-emerald-400">${total.toFixed(2)}</span>
          </div>
          <div className="flex gap-2">
            <Button variant="ghost" onClick={onClose} className="text-slate-300 hover:text-white">Cancelar</Button>
            <Button 
              onClick={() => mutation.mutate()} 
              disabled={mutation.isPending || items.length === 0}
              className="bg-cyan-600 hover:bg-cyan-500 text-white font-bold"
            >
              {mutation.isPending ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
              Generar Cotización
            </Button>
          </div>
        </div>

      </div>
    </div>
  );
}
