import { NextResponse } from 'next/server';
import { MOCK_INSIGHTS } from '@/types/insights';

export async function GET() {
  // En producción: Aquí harías una llamada a Ollama/LLM analizando el historial de chats
  // y el inventario actual para generar insights en tiempo real.
  return NextResponse.json({ insights: MOCK_INSIGHTS });
}

export async function POST(req: Request) {
  try {
    const { chatId, agentId, reason } = await req.json();
    // Lógica para asignar chat a humano en BD/Redis
    console.log(`🤝 Handover: Chat ${chatId} asignado a agente ${agentId}. Razón: ${reason}`);
    return NextResponse.json({ success: true });
  } catch (err) {
    return NextResponse.json({ success: false, error: 'Invalid payload' }, { status: 400 });
  }
}
