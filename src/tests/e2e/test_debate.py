import asyncio
import logging
from core.llm.router import llm_router
from services.agent_debate import AgentDebateOrchestrator

# Configurar logging para ver la salida en la terminal
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

async def main():
    print("\n" + "="*60)
    print("🤖 SIMULACIÓN DE DEBATE: OFICIAL DE RIESGOS VS VENTAS")
    print("="*60 + "\n")
    
    # Instanciar el Orquestador de Debate usando el LLMRouter (por defecto local)
    orchestrator = AgentDebateOrchestrator(llm_router=llm_router, provider="local")
    
    # Definir un escenario sospechoso (Fraude / Anomalía)
    topic = (
        "El cliente 'Juan Pérez' con cuenta nueva de hace 2 horas está intentando "
        "comprar 5 iPhones 15 Pro Max de contado usando 3 tarjetas de crédito "
        "diferentes emitidas en distintos países. El sistema antifraude arrojó "
        "un puntaje de riesgo de 85/100."
    )
    
    context = {
        "tenant_id": "tech-store-tenant-01",
        "order_amount": "$6000 USD",
        "customer_lifetime_value": "$0",
        "inventory_status": "Bajo stock para este artículo",
        "shipping_address": "Apartado de correos (P.O. Box) en Miami, FL"
    }
    
    print(f"📌 TÓPICO: {topic}\n")
    print(f"📦 CONTEXTO DE NEGOCIO: {context}\n")
    print("-" * 60)
    
    # Ejecutar el debate usando el escenario order_validation
    result = await orchestrator.run_debate(
        topic=topic,
        context=context,
        scenario_type="order_validation"
    )
    
    print("\n" + "="*60)
    print("⚖️ VEREDICTO FINAL DEL MODERADOR")
    print("="*60)
    print(f"Decisión: {result.verdict.name}")
    print(f"Confianza: {result.confidence * 100}%")
    print(f"Consenso alcanzado: {'Sí' if result.consensus_reached else 'No'}")
    print(f"Razonamiento: {result.reasoning}")
    print("="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
