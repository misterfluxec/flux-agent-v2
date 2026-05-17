'use client';

import { Order } from '@/services/api/commerce';
import { X, Package, Truck, MessageSquare, ExternalLink, Calendar, CreditCard, ChevronRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

interface OrderDetailsModalProps {
  order: Order | null;
  isOpen: boolean;
  onClose: () => void;
  onAction: (orderId: string, actionId: string) => void;
}

export default function OrderDetailsModal({ order, isOpen, onClose, onAction }: OrderDetailsModalProps) {
  if (!isOpen || !order) return null;

  // Mocked AI Chat history for the CRM concept
  const chatLogs = [
    { role: 'user', time: '10:45 AM', text: 'Hola, quería confirmar si tienen en stock los tenis model runner en talla 42.' },
    { role: 'assistant', time: '10:45 AM', text: '¡Hola! Sí, tenemos 3 pares disponibles en talla 42 (Color Negro y Azul). ¿Te gustaría que te reserve uno o procedemos con la compra?' },
    { role: 'user', time: '10:47 AM', text: 'Genial, procedamos con la compra por favor. Pago con tarjeta.' },
    { role: 'assistant', time: '10:47 AM', text: 'Perfecto. He generado tu link de pago seguro: https://pay.stripe/xxx. Una vez confirmado el pago, procesaremos el envío de inmediato.' }
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose}></div>
      <div className="relative bg-[#0a0a0f] border border-white/10 rounded-3xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col shadow-2xl animate-in zoom-in-95 duration-200">
        
        {/* Header */}
        <div className="p-6 border-b border-white/10 flex justify-between items-center bg-white/[0.02]">
          <div>
            <div className="flex items-center gap-3">
              <h2 className="text-2xl font-bold text-white/90">Orden #{order.id.slice(0, 8)}</h2>
              <Badge variant="outline" className="bg-cyan-500/10 text-cyan-400 border-cyan-500/20">{order.status}</Badge>
            </div>
            <p className="text-sm text-white/40 mt-1 flex items-center gap-2">
              <Calendar className="w-4 h-4" /> {new Date(order.created_at).toLocaleString()}
            </p>
          </div>
          <button onClick={onClose} className="p-2 text-white/40 hover:text-white/80 bg-white/5 hover:bg-white/10 rounded-xl transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-6 flex flex-col md:flex-row gap-6">
          
          {/* Left Column: Financials & Logistics */}
          <div className="w-full md:w-1/2 space-y-6">
            
            <div className="bg-white/5 border border-white/10 rounded-2xl p-5">
              <h3 className="font-bold text-white/80 mb-4 flex items-center gap-2">
                <CreditCard className="w-4 h-4 text-emerald-400" /> Resumen Financiero
              </h3>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between text-white/60">
                  <span>Subtotal</span>
                  <span>${(order.total_amount * 0.85).toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-white/60">
                  <span>Impuestos (15%)</span>
                  <span>${(order.total_amount * 0.15).toFixed(2)}</span>
                </div>
                <div className="flex justify-between font-bold text-lg text-emerald-400 pt-3 border-t border-white/10">
                  <span>Total</span>
                  <span>${order.total_amount.toFixed(2)}</span>
                </div>
              </div>
            </div>

            <div className="bg-white/5 border border-white/10 rounded-2xl p-5">
              <h3 className="font-bold text-white/80 mb-4 flex items-center gap-2">
                <Truck className="w-4 h-4 text-cyan-400" /> Logística
              </h3>
              <div className="space-y-4">
                <div className="bg-black/20 rounded-xl p-3 border border-white/5">
                  <p className="text-xs text-white/40 mb-1">Dirección de Envío</p>
                  <p className="text-sm text-white/80">Av. Siempre Viva 123, Sprinfield</p>
                </div>
                
                {/* Timeline mock */}
                <div className="relative pl-6 space-y-4 border-l border-white/10 ml-3">
                  <div className="relative">
                    <div className="absolute -left-[29px] top-1 w-3 h-3 bg-emerald-500 rounded-full shadow-[0_0_10px_rgba(16,185,129,0.5)]"></div>
                    <p className="text-xs font-bold text-emerald-400">Orden Creada</p>
                    <p className="text-[10px] text-white/40">10:48 AM</p>
                  </div>
                  <div className="relative">
                    <div className="absolute -left-[29px] top-1 w-3 h-3 bg-emerald-500 rounded-full shadow-[0_0_10px_rgba(16,185,129,0.5)]"></div>
                    <p className="text-xs font-bold text-emerald-400">Pago Confirmado</p>
                    <p className="text-[10px] text-white/40">10:52 AM</p>
                  </div>
                  <div className="relative">
                    <div className={`absolute -left-[29px] top-1 w-3 h-3 rounded-full ${order.status === 'shipped' || order.status === 'delivered' ? 'bg-cyan-500 shadow-[0_0_10px_rgba(6,182,212,0.5)]' : 'bg-white/20 border border-white/10'}`}></div>
                    <p className={`text-xs font-bold ${order.status === 'shipped' || order.status === 'delivered' ? 'text-cyan-400' : 'text-white/40'}`}>Enviado</p>
                  </div>
                </div>

              </div>
            </div>

            {/* Acciones */}
            <div className="bg-white/5 border border-white/10 rounded-2xl p-5">
              <h3 className="font-bold text-white/80 mb-4">Acciones de Orden</h3>
              <div className="flex flex-wrap gap-2">
                {order.available_actions?.map(action => (
                  <Button
                    key={action.id}
                    size="sm"
                    variant={action.variant === 'primary' ? 'default' : 'outline'}
                    onClick={() => onAction(order.id, action.id)}
                    className={`text-xs ${action.variant === 'primary' ? 'bg-cyan-500 hover:bg-cyan-600 text-white' : 'bg-transparent border-white/20 text-white/70 hover:bg-white/10 hover:text-white'}`}
                  >
                    {action.label}
                  </Button>
                ))}
              </div>
            </div>

          </div>

          {/* Right Column: AI Chat Log */}
          <div className="w-full md:w-1/2 flex flex-col h-full max-h-[600px] bg-black/40 rounded-2xl border border-white/5 overflow-hidden">
            <div className="p-4 border-b border-white/10 bg-white/[0.02] flex items-center justify-between">
              <h3 className="font-bold text-white/80 flex items-center gap-2">
                <MessageSquare className="w-4 h-4 text-purple-400" /> Log del Agente IA
              </h3>
              <span className="text-[10px] bg-purple-500/20 text-purple-400 px-2 py-0.5 rounded-full font-bold">Autónomo</span>
            </div>
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {chatLogs.map((log, idx) => (
                <div key={idx} className={`flex flex-col ${log.role === 'user' ? 'items-end' : 'items-start'}`}>
                  <div className={`max-w-[85%] p-3 rounded-2xl text-sm ${
                    log.role === 'user' 
                      ? 'bg-white/10 text-white rounded-br-sm' 
                      : 'bg-purple-500/10 border border-purple-500/20 text-purple-100 rounded-bl-sm'
                  }`}>
                    {log.text}
                  </div>
                  <span className="text-[10px] text-white/30 mt-1 px-1">{log.time}</span>
                </div>
              ))}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
