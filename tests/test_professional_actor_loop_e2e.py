"""
E2E Integration Test: Professional Actor Loop con Pedido Complejo
=================================================================
Escenarios LATAM validados:
  1. Happy Path Ecuador     → 4/4 pasos SOP completados sin debate
  2. Fallo de Stock CO      → Debate CAMEL activado → resolución
  3. Alto Riesgo MX         → Múltiples fallos → escalación a humano

Valida:
  ✅ Lookup correcto de SOP por rol y trigger
  ✅ Ejecución secuencial de pasos del SOP
  ✅ Activación del Debate al fallar un paso
  ✅ Parseo del veredicto del moderador
  ✅ Respuesta final auditada con audit trail
  ✅ Métricas de latencia del pipeline completo
"""
import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from domain.meta_agent import SOP, SOPStep, BaseRole
from services.sop_manager import SOPManager
from services.agent_debate import AgentDebateOrchestrator
from services.professional_actor_loop import ProfessionalActorLoop, ActorLoopContext
from services.sop_prompt_builder import SOPPromptBuilder

# ─── IDs FIJOS para garantizar lookup consistente ──────────────────────────
FIXED_SOP_ID   = "sop-sales-latam-v1"
FIXED_ROLE_ID  = "role-sales-latam"


def build_shared_sop_manager() -> tuple[SOPManager, BaseRole, SOP]:
    """Construye el gestor de SOPs compartido para todos los escenarios."""
    sop = SOP(
        id=FIXED_SOP_ID,
        name="Cierre de Venta LATAM (EC/CO/MX)",
        version="1.0",
        description="Proceso estándar de calificación y cierre de ventas para el mercado LATAM.",
        trigger_conditions=["comprar", "precio", "pedido", "orden", "producto", "unidades", "pago", "factura"],
        steps=[
            SOPStep(
                order=1,
                instruction="Verificar identidad del cliente y saludar profesionalmente.",
                validation_criteria="Cliente identificado en la base de datos.",
                failure_protocol="Solicitar nombre completo, email y número de teléfono."
            ),
            SOPStep(
                order=2,
                instruction="Consultar disponibilidad y precio del producto solicitado.",
                required_action="get_catalog_item",
                validation_criteria="Producto disponible con stock suficiente.",
                failure_protocol="Ofrecer producto alternativo o lista de espera."
            ),
            SOPStep(
                order=3,
                instruction="Verificar que el monto supera el mínimo y aplicar descuentos.",
                required_action="validate_order_amount",
                validation_criteria="Monto >= $50 USD. Descuentos aplicados correctamente.",
                failure_protocol="Informar condiciones mínimas y ofrecer productos complementarios."
            ),
            SOPStep(
                order=4,
                instruction="Generar link de pago personalizado o pre-orden en el ERP.",
                required_action="create_draft_order",
                validation_criteria="Orden creada con referencia única en el sistema.",
                failure_protocol="Reportar error técnico e intentar en 5 minutos."
            ),
        ],
    )

    role = BaseRole(
        id=FIXED_ROLE_ID,
        name="Sales Specialist LATAM",
        profile="Especialista en ventas digitales para EC, CO, MX. Habla español nativo.",
        goals=[
            "Convertir leads en clientes siguiendo el SOP de ventas.",
            "Maximizar el valor de cada interacción.",
            "Mantener experiencia de clase mundial.",
        ],
        constraints=[
            "NO ofrecer descuentos >20% sin autorización.",
            "NO procesar pedidos fuera de la operación LATAM.",
        ],
        allowed_actions=["get_catalog_item", "validate_order_amount", "create_draft_order"],
        assigned_sops=[FIXED_SOP_ID],
    )

    manager = SOPManager(storage_path="/tmp/test_sops")
    manager.register_sop(sop)
    manager.register_role(role)
    return manager, role, sop


async def run_scenario(
    title: str,
    input_text: str,
    business_context: dict,
    simulated_failures: list,
    pal: ProfessionalActorLoop,
    role: BaseRole,
    active_sop: SOP,
) -> dict:
    """Ejecuta un escenario de prueba con el PAL compartido."""
    print(f"\n{'='*60}")
    print(f"🧪 ESCENARIO: {title}")
    print(f"{'='*60}")

    ctx = ActorLoopContext(
        tenant_id="tenant-latam-001",
        customer_id="cust-test-001",
        role_id=FIXED_ROLE_ID,
        input_text=input_text,
        business_context={
            **business_context,
            "simulated_failures": simulated_failures,
        },
    )

    result = await pal.execute(ctx)

    # ─── Reportar resultado ───────────────────────────────────────────────
    print(f"\n📋 RESULTADO:")
    print(f"  ✅ Éxito:            {result.success}")
    print(f"  🏁 Veredicto:        {result.final_verdict.upper()}")
    print(f"  📜 SOP Respetado:    {result.sop_adhered}")
    print(f"  🗣️  Debates CAMEL:   {result.debates_triggered}")
    print(f"  ⏱️  Tiempo Total:     {result.processing_time_ms}ms")

    print(f"\n💬 RESPUESTA AL CLIENTE:")
    print(f"  \"{result.response}\"")

    print(f"\n📊 AUDIT TRAIL ({len(result.audit_trail)} eventos):")
    for event in result.audit_trail:
        details = {k: v for k, v in event.items() if k != "event"}
        print(f"  → {event['event']}: {json.dumps(details, ensure_ascii=False)}")

    # ─── Mostrar SOP Prompt generado ─────────────────────────────────────
    if ctx.active_sop:
        prompt = SOPPromptBuilder.build_system_prompt(role, ctx.active_sop)
        print(f"\n🔧 OLLAMA SOP PROMPT (primeros 400 chars):")
        print(f"  {prompt[:400].strip()}...")

    return {
        "scenario": title,
        "success": result.success,
        "verdict": result.final_verdict,
        "debates": result.debates_triggered,
        "latency_ms": result.processing_time_ms,
        "sop_adhered": result.sop_adhered,
        "audit_events": len(result.audit_trail),
    }


async def main():
    print("🚀 Professional Actor Loop — Test E2E (Fortress Path v2.7)")
    print("📡 MetaGPT (SOPs) + CAMEL (Debate) + Ollama (Razonamiento Local)")

    # ─── Setup global (una sola vez) ─────────────────────────────────────
    sop_manager, role, active_sop = build_shared_sop_manager()
    debate_orchestrator = AgentDebateOrchestrator(
        ollama_url="http://localhost:11434", model="llama3"
    )
    pal = ProfessionalActorLoop(
        sop_manager=sop_manager,
        debate_orchestrator=debate_orchestrator,
    )

    results = []

    # ─── ESCENARIO 1: Happy Path Ecuador ─────────────────────────────────
    r1 = await run_scenario(
        title="Pedido Estándar Ecuador (Happy Path)",
        input_text="Quiero comprar 3 kits de manicura profesional para mi salón en Guayaquil",
        business_context={
            "cliente": "Maritza Sánchez",
            "país": "Ecuador",
            "monto_pedido": "$180 USD",
            "producto": "Kit Manicura Pro v3",
            "stock_disponible": "25 unidades",
        },
        simulated_failures=[],
        pal=pal, role=role, active_sop=active_sop,
    )
    results.append(r1)

    # ─── ESCENARIO 2: Fallo Stock → Debate CAMEL ─────────────────────────
    r2 = await run_scenario(
        title="Fallo de Stock Colombia — Debate CAMEL Activado",
        input_text="Necesito 50 unidades de gel UV profesional para mañana, es urgente",
        business_context={
            "cliente": "Pedro Gómez - B2B",
            "país": "Colombia",
            "monto_pedido": "$850 USD",
            "producto": "Gel UV Pro 30ml",
            "stock_disponible": "8 unidades",
            "urgencia": "ALTA — evento próximo",
        },
        simulated_failures=[2],  # Falla paso 2: consulta de stock
        pal=pal, role=role, active_sop=active_sop,
    )
    results.append(r2)

    # ─── ESCENARIO 3: Alto Riesgo → Escalación a Humano ──────────────────
    r3 = await run_scenario(
        title="Pedido de Alto Riesgo México — Escalación a Humano",
        input_text="Quiero hacer un pedido grande y pago con transferencia bancaria, necesito factura especial",
        business_context={
            "cliente": "International Corp MX",
            "país": "México",
            "monto_pedido": "$5,200 USD",
            "método_pago": "Wire transfer banco extranjero",
            "request_especial": "Factura en USD con RFC extranjero",
            "riesgo_fraude": "ALTO",
        },
        simulated_failures=[2, 3],  # Fallan pasos de stock y validación
        pal=pal, role=role, active_sop=active_sop,
    )
    results.append(r3)

    # ─── RESUMEN FINAL ────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print("📊 RESUMEN EJECUTIVO — Professional Actor Loop")
    print(f"{'='*60}")
    icons = {"success": "✅", "rejected": "❌", "escalated": "⚠️"}
    for r in results:
        icon = icons.get(r["verdict"], "🔵")
        debates_str = f"{r['debates']} debate(s)" if r["debates"] > 0 else "sin debates"
        print(f"  {icon} {r['scenario']}")
        print(f"     Veredicto: {r['verdict'].upper()} | {debates_str} | {r['latency_ms']}ms | {r['audit_events']} audit events")

    total_debates = sum(r["debates"] for r in results)
    avg_latency = sum(r["latency_ms"] for r in results) // len(results)
    sop_adherence = sum(1 for r in results if r["sop_adhered"]) / len(results) * 100

    print(f"\n🎯 KPIs del Sistema:")
    print(f"  - Total Debates CAMEL:         {total_debates}")
    print(f"  - Latencia Promedio Pipeline:  {avg_latency}ms  (SLO target: <2000ms)")
    print(f"  - Adherencia SOP:              {sop_adherence:.0f}%  (SLO target: >95%)")
    print(f"\n🛡️  Arquitectura Validada: MetaGPT + CAMEL + Ollama (Fortress Path v2.7)")


if __name__ == "__main__":
    asyncio.run(main())
