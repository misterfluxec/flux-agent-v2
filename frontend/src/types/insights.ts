export type Sentiment = 'positive' | 'neutral' | 'negative';
export type InsightType = 'stock_alert' | 'sales_opportunity' | 'sentiment_drop' | 'trend';

export interface AIInsight {
  id: string;
  type: InsightType;
  title: string;
  message: string;
  confidence: number; // 0-1
  actionRequired: boolean;
  timestamp: string;
}

export interface ChatHandover {
  chatId: string;
  assignedTo: string; // ID del humano
  status: 'pending' | 'accepted' | 'resolved';
  reason: string;
}

export const MOCK_INSIGHTS: AIInsight[] = [
  {
    id: '1', type: 'stock_alert', title: '⚠️ Alerta de Stock Bajo',
    message: 'Yanua detectó que las "Zapatillas Nike Air" están por agotarse (3 unidades). Se recomienda reponer antes de mañana.',
    confidence: 0.95, actionRequired: true, timestamp: '2026-05-05T14:00:00Z'
  },
  {
    id: '2', type: 'sentiment_drop', title: '📉 Caída de Sentimiento',
    message: 'El 15% de las conversaciones en Telegram hoy tuvieron tone negativo. Revisa los tiempos de respuesta.',
    confidence: 0.88, actionRequired: false, timestamp: '2026-05-05T13:30:00Z'
  },
  {
    id: '3', type: 'sales_opportunity', title: '🔥 Oportunidad de Venta',
    message: '3 clientes preguntaron por "Ofertas de Fin de Semana". Yanua sugiere activar una campaña de descuentos.',
    confidence: 0.92, actionRequired: true, timestamp: '2026-05-05T12:15:00Z'
  }
];
