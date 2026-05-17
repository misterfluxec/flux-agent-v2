'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { getOrders, fulfillOrder, generateReceipt, Order, OrderAction } from '@/services/api/commerce';
import {
  Package, Loader2, Clock, CheckCircle2, Truck, XCircle,
  CreditCard, Search, ArrowUpRight, Play, FileText
} from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { DragDropContext, Droppable, Draggable, DropResult } from '@hello-pangea/dnd';
import { Button } from '@/components/ui/button';
import OrderDetailsModal from './components/OrderDetailsModal';

// ─── ORDER STATUS CONFIG ─────────────────────────────────────────────────
const ORDER_STATUS: Record<string, { label: string; icon: any; color: string }> = {
  pending:    { label: 'Pendiente',   icon: Clock,          color: 'bg-amber-500/10 text-amber-400 border-amber-500/20' },
  confirmed:  { label: 'Confirmada',  icon: CheckCircle2,   color: 'bg-blue-500/10 text-blue-400 border-blue-500/20' },
  processing: { label: 'Procesando',  icon: Loader2,        color: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20' },
  paid:       { label: 'Cobrada',     icon: CreditCard,     color: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' },
  shipped:    { label: 'Enviada',     icon: Truck,          color: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20' },
  delivered:  { label: 'Entregada',   icon: CheckCircle2,   color: 'bg-teal-500/10 text-teal-400 border-teal-500/20' },
  completed:  { label: 'Completada',  icon: CheckCircle2,   color: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' },
  cancelled:  { label: 'Cancelada',   icon: XCircle,        color: 'bg-red-500/10 text-red-400 border-red-500/20' },
  refunded:   { label: 'Reembolsada', icon: XCircle,        color: 'bg-red-500/10 text-red-400 border-red-500/20' },
};

const PAYMENT_STATUS: Record<string, { label: string; color: string }> = {
  pending:  { label: 'Sin pago',  color: 'bg-white/5 text-white/40 border-white/10' },
  paid:     { label: 'Pagado',    color: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' },
  refunded: { label: 'Reembolso', color: 'bg-amber-500/10 text-amber-400 border-amber-500/20' },
};

export default function OrdersPage() {
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const queryClient = useQueryClient();
  const router = useRouter();
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);

  const { data: orders = [], isLoading } = useQuery({
    queryKey: ['orders'],
    queryFn: () => getOrders(),
  });

  const fulfillMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) => fulfillOrder(id, { status }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['orders'] })
  });

  const receiptMutation = useMutation({
    mutationFn: (id: string) => generateReceipt(id),
    onSuccess: (data: any) => {
      // Redirigir al prototipo de factura operacional
      router.push(`/dashboard/receipt/${data.invoice_id}`);
    }
  });

  const handleAction = (orderId: string, actionId: string) => {
    if (actionId === 'generate_receipt') {
      receiptMutation.mutate(orderId);
    } else if (actionId === 'ship') {
      fulfillMutation.mutate({ id: orderId, status: 'shipped' });
    } else if (actionId === 'deliver') {
      fulfillMutation.mutate({ id: orderId, status: 'delivered' });
    }
  };

  const filtered = orders
    .filter((o: Order) => statusFilter === 'all' || o.status === statusFilter)
    .filter((o: Order) => search === '' || o.id.includes(search) || o.customer_id?.includes(search));

  // Revenue summary
  const totalRevenue = orders
    .filter((o: Order) => o.status === 'paid' || o.status === 'shipped' || o.status === 'delivered' || o.status === 'completed')
    .reduce((sum: number, o: Order) => sum + (o.total_amount || 0), 0);

  const counts = {
    total: orders.length,
    pending: orders.filter((o: Order) => o.status === 'pending').length,
    paid: orders.filter((o: Order) => o.status === 'paid' || o.status === 'shipped' || o.status === 'delivered' || o.status === 'completed').length,
  };

  // Kanban Columns Definition
  const columns = [
    { id: 'pending', title: 'Pendientes', color: 'border-amber-500/20 bg-amber-500/[0.02]', dot: 'bg-amber-400' },
    { id: 'paid', title: 'Cobradas / Prep.', color: 'border-emerald-500/20 bg-emerald-500/[0.02]', dot: 'bg-emerald-400' },
    { id: 'shipped', title: 'En Tránsito', color: 'border-cyan-500/20 bg-cyan-500/[0.02]', dot: 'bg-cyan-400' },
    { id: 'delivered', title: 'Entregadas', color: 'border-teal-500/20 bg-teal-500/[0.02]', dot: 'bg-teal-400' },
  ];

  const getOrdersByStatus = (status: string) => {
    // Group "processing" into "paid", and "completed" into "delivered" for visual simplicity
    return filtered.filter((o: Order) => {
      if (status === 'paid') return ['paid', 'processing'].includes(o.status);
      if (status === 'delivered') return ['delivered', 'completed'].includes(o.status);
      return o.status === status;
    });
  };

  const onDragEnd = (result: DropResult) => {
    if (!result.destination) return;
    const { source, destination, draggableId } = result;
    if (source.droppableId !== destination.droppableId) {
      fulfillMutation.mutate({ id: draggableId, status: destination.droppableId });
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-500 pb-12 px-6 md:px-8 max-w-[1400px] mx-auto pt-6 h-screen flex flex-col">
      <OrderDetailsModal 
        order={selectedOrder} 
        isOpen={!!selectedOrder} 
        onClose={() => setSelectedOrder(null)} 
        onAction={handleAction}
      />

      {/* Header */}
      <div className="flex flex-col md:flex-row items-start md:items-end justify-between gap-5">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Package className="w-4 h-4 text-cyan-400" />
            <span className="text-[10px] font-bold uppercase tracking-widest text-cyan-400/80">Órdenes de Venta</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white/80">
            Órdenes
          </h1>
          <p className="text-sm text-white/40 mt-1">
            Pedidos confirmados — tracking de status y pagos
          </p>
        </div>

        {/* Revenue Card */}
        <div className="bg-emerald-500/[0.06] border border-emerald-500/[0.12] rounded-2xl p-4 pr-10 relative overflow-hidden">
          <p className="text-[11px] font-bold text-emerald-400/50 uppercase tracking-widest mb-1">Revenue Confirmado</p>
          <div className="flex items-end gap-3">
            <h2 className="text-2xl font-black text-white/80 tabular-nums">${totalRevenue.toFixed(2)}</h2>
            <span className="text-[13px] font-semibold text-emerald-400/80 flex items-center mb-0.5">
              <ArrowUpRight className="w-3.5 h-3.5 mr-0.5" /> {counts.paid} cobradas
            </span>
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-white/[0.02] border border-white/[0.05] rounded-xl p-4 text-center">
          <p className="text-2xl font-black text-white/80">{counts.total}</p>
          <p className="text-[11px] text-white/30 font-medium mt-1">Total Órdenes</p>
        </div>
        <div className="bg-amber-500/[0.04] border border-amber-500/[0.08] rounded-xl p-4 text-center">
          <p className="text-2xl font-black text-amber-400">{counts.pending}</p>
          <p className="text-[11px] text-white/30 font-medium mt-1">Pendientes</p>
        </div>
        <div className="bg-emerald-500/[0.04] border border-emerald-500/[0.08] rounded-xl p-4 text-center">
          <p className="text-2xl font-black text-emerald-400">{counts.paid}</p>
          <p className="text-[11px] text-white/30 font-medium mt-1">Cobradas</p>
        </div>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" />
        <Input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Buscar por ID de sort_order o cliente..."
          className="pl-11 h-12 bg-white/[0.03] border-white/[0.06] rounded-xl text-white placeholder:text-white/20 focus:border-cyan-500/30"
        />
      </div>

      {/* Filter Tabs & View Toggle */}
      <div className="flex items-center justify-between pb-1">
        <div className="flex items-center gap-2 overflow-x-auto">
          {[{ key: 'all', label: 'Todas' }, { key: 'pending', label: 'Pendientes' }, { key: 'paid', label: 'Pagadas' }, { key: 'shipped', label: 'Enviadas' }].map(tab => (
            <button
              key={tab.key}
              onClick={() => setStatusFilter(tab.key)}
              className={`px-4 py-2 text-xs font-bold rounded-xl border transition-all ${
                statusFilter === tab.key
                  ? 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20'
                  : 'bg-white/[0.02] text-white/40 border-white/[0.05] hover:border-white/10'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Kanban Board */}
      {isLoading ? (
        <div className="flex-1 flex flex-col items-center justify-center text-white/30">
          <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4 text-cyan-500" />
          <p>Cargando pipeline de órdenes...</p>
        </div>
      ) : (
        <DragDropContext onDragEnd={onDragEnd}>
          <div className="flex-1 grid grid-cols-1 md:grid-cols-4 gap-6 min-h-[600px]">
            {columns.map(col => {
              const colOrders = getOrdersByStatus(col.id);
              return (
                <div key={col.id} className={`flex flex-col rounded-2xl border ${col.color} overflow-hidden bg-[#111827]`}>
                  <div className="p-4 border-b border-white/5 flex justify-between items-center bg-white/[0.01]">
                    <div className="flex items-center gap-2">
                      <div className={`w-2.5 h-2.5 rounded-full ${col.dot}`}></div>
                      <h3 className="font-bold text-white/80">{col.title}</h3>
                    </div>
                    <Badge variant="outline" className="bg-white/5 text-white/50 border-white/10">
                      {colOrders.length}
                    </Badge>
                  </div>
                  
                  <Droppable droppableId={col.id}>
                    {(provided, snapshot) => (
                      <div
                        {...provided.droppableProps}
                        ref={provided.innerRef}
                        className={`flex-1 p-3 space-y-3 overflow-y-auto transition-colors ${snapshot.isDraggingOver ? 'bg-white/[0.03]' : ''}`}
                      >
                        {colOrders.map((order: Order, index: number) => {
                          const paymentConf = PAYMENT_STATUS[order.payment_status || 'pending'] || PAYMENT_STATUS.pending;
                          return (
                            <Draggable key={order.id} draggableId={order.id} index={index}>
                              {(provided, snapshot) => (
                                <div
                                  ref={provided.innerRef}
                                  {...provided.draggableProps}
                                  {...provided.dragHandleProps}
                                  onClick={() => setSelectedOrder(order)}
                                  className={`p-4 rounded-xl border transition-all cursor-pointer ${
                                    snapshot.isDragging ? 'bg-[#1f2937] border-cyan-500/50 shadow-2xl scale-105 z-50' : 'bg-white/[0.02] border-white/[0.05] hover:border-white/20 hover:bg-white/[0.04]'
                                  }`}
                                >
                                  <div className="flex justify-between items-start mb-2">
                                    <span className="text-[10px] font-mono text-white/40">#{order.id.slice(0, 8)}</span>
                                    <span className={`px-2 py-0.5 text-[9px] font-bold rounded border ${paymentConf.color}`}>
                                      {paymentConf.label}
                                    </span>
                                  </div>
                                  <div className="text-sm text-white/70 font-medium truncate mb-3">
                                    {order.customer_id?.slice(0, 15) || 'Cliente Anon.'}...
                                  </div>
                                  <div className="flex justify-between items-end">
                                    <div className="text-xs text-white/30">
                                      {new Date(order.created_at).toLocaleDateString()}
                                    </div>
                                    <div className="text-[15px] font-black text-white/90 tabular-nums">
                                      ${order.total_amount?.toFixed(2) || '0.00'}
                                    </div>
                                  </div>
                                </div>
                              )}
                            </Draggable>
                          );
                        })}
                        {provided.placeholder}
                        {colOrders.length === 0 && !snapshot.isDraggingOver && (
                          <div className="h-24 border border-dashed border-white/10 rounded-xl flex items-center justify-center text-white/20 text-xs font-medium">
                            Soltar aquí
                          </div>
                        )}
                      </div>
                    )}
                  </Droppable>
                </div>
              );
            })}
          </div>
        </DragDropContext>
      )}
    </div>
  );
}
