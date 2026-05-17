'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getPromotions, createPromotion, deletePromotion, CatalogPromotion } from '@/services/api/commerce';
import { Tag, Plus, Loader2, Calendar, Trash2, Percent } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';

export default function PromotionsTab() {
  const queryClient = useQueryClient();
  const [isCreating, setIsCreating] = useState(false);
  const [newPromo, setNewPromo] = useState({
    name: '',
    discount_type: 'percentage' as 'percentage' | 'fixed_amount',
    discount_value: 0,
    start_date: new Date().toISOString().split('T')[0],
    end_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    is_active: true
  });

  const { data: promotions = [], isLoading } = useQuery({
    queryKey: ['promotions'],
    queryFn: getPromotions,
  });

  const createMutation = useMutation({
    mutationFn: () => createPromotion(newPromo as any),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['promotions'] });
      toast.success('Promoción creada exitosamente');
      setIsCreating(false);
    },
    onError: () => toast.error('Error al crear la promoción')
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deletePromotion(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['promotions'] });
      toast.success('Promoción eliminada');
    }
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createMutation.mutate();
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-white/30">
        <Loader2 className="w-8 h-8 animate-spin mb-4 text-cyan-500" />
        <p>Cargando promociones...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-xl font-bold text-white/80 flex items-center gap-2">
            <Tag className="w-5 h-5 text-purple-400" /> Reglas de Promoción
          </h2>
          <p className="text-sm text-white/40">La IA usará estas reglas fijas para ofrecer descuentos a tus clientes.</p>
        </div>
        <Button 
          onClick={() => setIsCreating(!isCreating)}
          className="bg-purple-600 hover:bg-purple-500 text-white"
        >
          {isCreating ? 'Cancelar' : <><Plus className="w-4 h-4 mr-2" /> Nueva Regla</>}
        </Button>
      </div>

      {isCreating && (
        <form onSubmit={handleSubmit} className="bg-white/[0.02] border border-purple-500/20 rounded-2xl p-6 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-white/50 mb-1 block">Nombre de la Promoción (Ej. Black Friday)</label>
              <Input required value={newPromo.name} onChange={e => setNewPromo({...newPromo, name: e.target.value})} className="bg-white/5 border-white/10" />
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="text-xs text-white/50 mb-1 block">Tipo</label>
                <select 
                  className="w-full h-10 px-3 rounded-md bg-white/5 border border-white/10 text-sm text-white focus:outline-none focus:border-purple-500/50"
                  value={newPromo.discount_type}
                  onChange={e => setNewPromo({...newPromo, discount_type: e.target.value as any})}
                >
                  <option value="percentage">Porcentaje (%)</option>
                  <option value="fixed_amount">Monto Fijo ($)</option>
                </select>
              </div>
              <div>
                <label className="text-xs text-white/50 mb-1 block">Valor</label>
                <Input required type="number" min="1" value={newPromo.discount_value} onChange={e => setNewPromo({...newPromo, discount_value: Number(e.target.value)})} className="bg-white/5 border-white/10" />
              </div>
            </div>
            <div>
              <label className="text-xs text-white/50 mb-1 block">Fecha Inicio</label>
              <Input required type="date" value={newPromo.start_date} onChange={e => setNewPromo({...newPromo, start_date: e.target.value})} className="bg-white/5 border-white/10 [color-scheme:dark]" />
            </div>
            <div>
              <label className="text-xs text-white/50 mb-1 block">Fecha Fin</label>
              <Input required type="date" value={newPromo.end_date} onChange={e => setNewPromo({...newPromo, end_date: e.target.value})} className="bg-white/5 border-white/10 [color-scheme:dark]" />
            </div>
          </div>
          <div className="flex justify-end pt-2">
            <Button type="submit" disabled={createMutation.isPending} className="bg-purple-600 hover:bg-purple-500 text-white">
              {createMutation.isPending ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : 'Guardar Regla'}
            </Button>
          </div>
        </form>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {promotions.length === 0 && !isCreating && (
          <div className="col-span-full py-12 text-center border border-dashed border-white/10 rounded-2xl">
            <Percent className="w-8 h-8 mx-auto mb-3 text-white/20" />
            <p className="text-white/40">No hay promociones activas.</p>
          </div>
        )}
        {promotions.map((promo: CatalogPromotion) => (
          <div key={promo.id} className="bg-[#111827] border border-white/5 rounded-2xl p-5 hover:border-purple-500/30 transition-all group relative overflow-hidden">
            <div className={`absolute top-0 right-0 w-2 h-full ${promo.is_active ? 'bg-emerald-500' : 'bg-red-500'}`}></div>
            <div className="flex justify-between items-start mb-3">
              <h3 className="font-bold text-white/90 text-lg">{promo.name}</h3>
              <Badge variant="outline" className={promo.discount_type === 'percentage' ? 'bg-purple-500/10 text-purple-400' : 'bg-cyan-500/10 text-cyan-400'}>
                {promo.discount_type === 'percentage' ? `${promo.discount_value}% OFF` : `$${promo.discount_value} OFF`}
              </Badge>
            </div>
            <div className="space-y-2 mt-4 text-xs text-white/50">
              <div className="flex items-center gap-2">
                <Calendar className="w-3.5 h-3.5" />
                <span>{promo.start_date} a {promo.end_date}</span>
              </div>
              <div className="flex items-center justify-between pt-2">
                <span className={promo.is_active ? 'text-emerald-400' : 'text-red-400'}>
                  {promo.is_active ? 'Activa' : 'Inactiva'}
                </span>
                <Button 
                  size="icon" 
                  variant="ghost" 
                  onClick={() => deleteMutation.mutate(promo.id)}
                  className="h-7 w-7 text-white/20 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  {deleteMutation.isPending ? <Loader2 className="w-3 h-3 animate-spin" /> : <Trash2 className="w-3 h-3" />}
                </Button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
