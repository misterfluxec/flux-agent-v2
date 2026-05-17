// =============================================================================
// MOCK API — Endpoints pendientes de implementación en backend
// Swap a producción: cambiar USE_MOCKS a false cuando el backend esté listo
// Ref: docs/specs/YANUA_GOVERNANCE_SPEC.md
// =============================================================================

export const USE_MOCKS = process.env.NODE_ENV !== "production";

// ─── Mock: /api/v1/yana/explain ──────────────────────────────────────────────

export interface ExplanationResponse {
  signals: string[];
  policy_applied: string;
  source: string;
  confidence_pct: number;
  reasoning_summary: string;
}

const MOCK_EXPLANATIONS: Record<string, ExplanationResponse> = {
  lead: {
    signals: [
      "Sentimiento positivo detectado en 4 de 5 mensajes",
      "Preguntó por price y disponibilidad en <10 min",
      "Historial: 2 visitas previas al catálogo",
      "Tiempo de respuesta del lead: <45 segundos",
    ],
    policy_applied: "lead_hot_threshold (score ≥ 80)",
    source: "Memoria episódica + Catálogo RAG v3",
    confidence_pct: 92,
    reasoning_summary: "Lead clasificado como HOT por alta intención de compra y engagement is_active.",
  },
  response: {
    signals: [
      "Coincidencia semántica >0.87 con FAQ de Garantías",
      "Fragmento extraído de: garantias_2024.pdf (pág. 3)",
      "Verificado contra catálogo de productos activos",
    ],
    policy_applied: "rag_retrieval_confidence (umbral: 0.75)",
    source: "RAG — garantias_2024.pdf + productos_activos.csv",
    confidence_pct: 88,
    reasoning_summary: "Respuesta generada a partir del documento de garantías actualizado.",
  },
  handoff: {
    signals: [
      "Sentimiento negativo detectado (frustración explícita)",
      "Solicitud de descuento >20% (fuera de política autónoma)",
      "Tercer intento de respuesta sin resolución satisfactoria",
    ],
    policy_applied: "REQUIRE_APPROVAL — discount_request >15%",
    source: "Policy Engine + Sentiment Analyzer",
    confidence_pct: 97,
    reasoning_summary: "Yanua solicitó intervención porque la situación requiere autorización humana.",
  },
};

export async function mockExplain(
  context: "lead" | "response" | "handoff",
  _entityId: string
): Promise<ExplanationResponse> {
  // Simula latencia de red
  await new Promise(r => setTimeout(r, 600));
  return MOCK_EXPLANATIONS[context] || MOCK_EXPLANATIONS.lead;
}

// ─── Mock: /api/v1/insights/recommendations ──────────────────────────────────

export interface Insight {
  id: string;
  type: "hot_lead" | "ia_gap" | "performance" | "task";
  title: string;
  context: string;
  priority: "high" | "medium" | "low";
  actions: { label: string; variant: "primary" | "secondary" | "dismiss"; href?: string }[];
}

export const MOCK_INSIGHTS: Insight[] = [
  {
    id: "ins_001",
    type: "ia_gap",
    title: "Yanua falla en preguntas sobre garantías",
    context: "3 leads no recibieron respuesta clara en las últimas 24h. Sube el PDF actualizado de garantías.",
    priority: "high",
    actions: [
      { label: "📤 Subir documento", variant: "primary", href: "/dashboard/data-ingestion" },
      { label: "👁️ Ver conversaciones", variant: "secondary", href: "/dashboard/conversations" },
      { label: "Ignorar", variant: "dismiss" },
    ],
  },
  {
    id: "ins_002",
    type: "hot_lead",
    title: "3 leads calientes sin respuesta humana",
    context: "Score promedio: 87. Llevan más de 15 min esperando. Riesgo de perder oportunidad.",
    priority: "high",
    actions: [
      { label: "🔥 Ir a Operaciones", variant: "primary", href: "/dashboard/conversations" },
      { label: "Ignorar", variant: "dismiss" },
    ],
  },
  {
    id: "ins_003",
    type: "performance",
    title: "Agente 'Vendedor Pro' convirtió 32% mejor esta semana",
    context: "Considera asignarle más channels o clonar su configuración para los nuevos agentes.",
    priority: "medium",
    actions: [
      { label: "📈 Ver Workforce IA", variant: "primary", href: "/dashboard/agents" },
      { label: "Ignorar", variant: "dismiss" },
    ],
  },
];

export async function mockRecommendations(): Promise<Insight[]> {
  await new Promise(r => setTimeout(r, 400));
  return MOCK_INSIGHTS;
}
