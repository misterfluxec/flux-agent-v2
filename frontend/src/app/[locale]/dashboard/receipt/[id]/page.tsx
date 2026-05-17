'use client';

import { useQuery } from '@tanstack/react-query';
import { getInvoice } from '@/services/api/commerce';
import { Loader2, Printer, ArrowLeft, Download } from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';

export default function ReceiptPage({ params }: { params: { id: string, locale: string } }) {
  const { data: invoice, isLoading, error } = useQuery({
    queryKey: ['invoice', params.id],
    queryFn: () => getInvoice(params.id),
    retry: false
  });

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <Loader2 className="w-8 h-8 animate-spin text-cyan-400 mb-4" />
        <p className="text-white/40">Cargando comprobante...</p>
      </div>
    );
  }

  if (error || !invoice) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <p className="text-red-400 font-bold mb-2">Comprobante no encontrado</p>
        <Link href={`/${params.locale}/dashboard/orders`}>
          <Button variant="outline" className="mt-4">
            Volver a Órdenes
          </Button>
        </Link>
      </div>
    );
  }

  const snapshot = typeof invoice.snapshot_data === 'string' 
    ? JSON.parse(invoice.snapshot_data) 
    : invoice.snapshot_data;

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="min-h-screen bg-gray-950 print:bg-white print:min-h-0 print:p-0">
      
      {/* ─── CONTROLES DE PANTALLA (No Imprimibles) ─── */}
      <div className="max-w-4xl mx-auto px-6 py-8 print:hidden flex items-center justify-between">
        <Link href={`/${params.locale}/dashboard/orders`} className="text-white/40 hover:text-white flex items-center gap-2 transition-colors text-sm">
          <ArrowLeft className="w-4 h-4" />
          Volver a Órdenes
        </Link>
        <div className="flex items-center gap-3">
          <Button variant="outline" onClick={handlePrint} className="bg-white/5 border-white/10 hover:bg-white/10 text-white">
            <Printer className="w-4 h-4 mr-2" />
            Imprimir
          </Button>
        </div>
      </div>

      {/* ─── DOCUMENTO (A4 Aspect, Imprimible) ─── */}
      <div className="max-w-4xl mx-auto px-6 pb-24 print:p-0 print:m-0 print:w-full print:max-w-none">
        
        <div className="bg-[#1e293b] print:bg-white rounded-2xl shadow-2xl overflow-hidden border border-white/10 print:border-none print:shadow-none">
          
          {/* Header */}
          <div className="p-8 md:p-12 border-b border-white/10 print:border-gray-200 flex flex-col md:flex-row justify-between items-start md:items-end gap-6">
            <div>
              <h1 className="text-3xl font-black text-white print:text-gray-900 tracking-tight">
                COMPROBANTE
              </h1>
              <h2 className="text-[11px] font-bold text-cyan-400 print:text-gray-500 uppercase tracking-widest mt-1">
                OPERACIONAL
              </h2>
            </div>
            
            <div className="text-left md:text-right">
              <p className="text-sm font-bold text-white print:text-gray-900">{snapshot.company?.name || 'FluxAgent Commerce'}</p>
              <p className="text-xs text-white/50 print:text-gray-500 mt-1">{snapshot.company?.address || 'B2B Fulfillment Center'}</p>
            </div>
          </div>

          {/* Metadata */}
          <div className="p-8 md:p-12 bg-black/20 print:bg-gray-50 grid grid-cols-2 md:grid-cols-4 gap-6 border-b border-white/10 print:border-gray-200">
            <div>
              <p className="text-[10px] uppercase font-bold text-white/40 print:text-gray-400 tracking-widest mb-1">Recibo N°</p>
              <p className="text-sm font-mono text-white print:text-gray-900">{invoice.receipt_number}</p>
            </div>
            <div>
              <p className="text-[10px] uppercase font-bold text-white/40 print:text-gray-400 tracking-widest mb-1">Orden Ref.</p>
              <p className="text-sm font-mono text-white print:text-gray-900">#{invoice.order_id.slice(0,8)}</p>
            </div>
            <div>
              <p className="text-[10px] uppercase font-bold text-white/40 print:text-gray-400 tracking-widest mb-1">Fecha Emisión</p>
              <p className="text-sm font-medium text-white print:text-gray-900">
                {new Date(invoice.issued_at).toLocaleDateString()}
              </p>
            </div>
            <div>
              <p className="text-[10px] uppercase font-bold text-white/40 print:text-gray-400 tracking-widest mb-1">Cliente</p>
              <p className="text-sm font-medium text-white print:text-gray-900">
                {snapshot.customer?.id?.slice(0, 12) || 'Consumidor Final'}
              </p>
            </div>
          </div>

          {/* Line Items (MVP: Muestra solo total si no hay items guardados) */}
          <div className="p-8 md:p-12">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-white/10 print:border-gray-200">
                  <th className="pb-3 text-[11px] font-bold text-white/40 print:text-gray-500 uppercase tracking-widest">Descripción</th>
                  <th className="pb-3 text-[11px] font-bold text-white/40 print:text-gray-500 uppercase tracking-widest text-right">Total</th>
                </tr>
              </thead>
              <tbody>
                {snapshot.items && snapshot.items.length > 0 ? (
                  snapshot.items.map((item: any, i: number) => (
                    <tr key={i} className="border-b border-white/5 print:border-gray-100">
                      <td className="py-4 text-sm text-white/80 print:text-gray-800">{item.name || 'Item'}</td>
                      <td className="py-4 text-sm font-mono text-right text-white/80 print:text-gray-800">
                        {snapshot.pricing?.currency} {(item.price * (item.quantity || 1)).toFixed(2)}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr className="border-b border-white/5 print:border-gray-100">
                    <td className="py-4 text-sm text-white/80 print:text-gray-800 font-medium">Pago por Orden #{invoice.order_id.slice(0,8)}</td>
                    <td className="py-4 text-sm font-mono text-right text-white/80 print:text-gray-800">
                      {snapshot.pricing?.currency} {invoice.total_amount.toFixed(2)}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>

            {/* Totals */}
            <div className="flex justify-end mt-8">
              <div className="w-full md:w-1/2 space-y-3">
                <div className="flex justify-between items-center text-sm">
                  <span className="text-white/60 print:text-gray-600">Subtotal</span>
                  <span className="text-white print:text-gray-900 font-mono">{snapshot.pricing?.currency} {invoice.total_amount.toFixed(2)}</span>
                </div>
                <div className="flex justify-between items-center pt-4 border-t border-white/10 print:border-gray-200">
                  <span className="text-base font-bold text-white print:text-gray-900">Total Pagado</span>
                  <span className="text-xl font-black text-emerald-400 print:text-gray-900 tabular-nums">
                    {snapshot.pricing?.currency} {invoice.total_amount.toFixed(2)}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Legal / Footer */}
          <div className="p-8 md:p-12 bg-white/5 print:bg-white border-t border-white/10 print:border-gray-200">
            <p className="text-xs text-white/40 print:text-gray-500 text-center leading-relaxed">
              {snapshot.legal?.disclaimer || 'Documento Operacional - Sin Valor Tributario.'}
            </p>
          </div>
        </div>
        
      </div>
    </div>
  );
}
