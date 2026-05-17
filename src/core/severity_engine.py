"""
Operational Severity Engine

Calcula automáticamente la severidad de un evento basándose en:
  1. Reglas estáticas por type de evento (base)
  2. Modificadores contextuales dinámicos (SLA, VIP, recurrencia)
  3. Escalada temporal (un evento "medium" puede escalar a "high" si no se atiende)

El backend enriquece cada evento ANTES de persistir.
El frontend recibe la severidad calculada — no la calcula él.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple


# =============================================================================
# Orden numérico de severidad (para comparaciones y escalada)
# =============================================================================
SEVERITY_RANK: Dict[str, int] = {
    "low": 0,
    "medium": 1,
    "high": 2,
    "critical": 3,
}

SEVERITY_FROM_RANK: Dict[int, str] = {v: k for k, v in SEVERITY_RANK.items()}


def _rank(sev: str) -> int:
    return SEVERITY_RANK.get(sev, 0)


def _max_sev(a: str, b: str) -> str:
    return SEVERITY_FROM_RANK[max(_rank(a), _rank(b))]


# =============================================================================
# 1. Reglas base por type de evento
# "Verdad de negocio" para FluxAgent — revisable con el equipo comercial.
# =============================================================================
BASE_SEVERITY_RULES: Dict[str, str] = {
    # Pagos — siempre crítico
    "payment.completed":        "critical",
    "payment.failed":           "critical",

    # Comercio de alto valor
    "order.created":            "high",
    "quote.accepted":           "high",
    "booking.confirmed":        "high",

    # Operaciones que requieren respuesta humana
    "handoff.requested":        "high",
    "alert.urgent":             "high",

    # Actividad comercial media
    "quote.generated":          "medium",
    "lead.qualified":           "medium",
    "lead.created":             "medium",
    "booking.cancelled":        "medium",
    "alert.ia_detected":        "medium",

    # Billing
    "billing.alert":            "critical",
    "tenant.quota_exhausted":   "high",
    "billing.threshold_reached":"high",

    # Automatizaciones y follow_ups
    "followup.scheduled":       "low",
    "followup.sent":            "low",
    "handoff.completed":        "low",

    # Conversación estándar
    "message.received":         "low",
    "message.sent":             "low",
    "conversation.started":     "low",
    "conversation.closed":      "low",

    # Sistema/voz
    "tool.executed":            "low",
    "voice.call_started":       "low",
    "voice.call_ended":         "low",
    "orchestrator.started":     "low",
    "policy.violation":         "high",
}

# business_impact canónico por categoría de evento
BUSINESS_IMPACT_MAP: Dict[str, str] = {
    "payment.completed":        "revenue",
    "payment.failed":           "revenue",
    "order.created":            "revenue",
    "quote.accepted":           "revenue",
    "quote.generated":          "revenue",
    "lead.qualified":           "revenue",
    "lead.created":             "revenue",
    "booking.confirmed":        "revenue",
    "booking.cancelled":        "retention",
    "handoff.requested":        "ops",
    "handoff.completed":        "ops",
    "followup.scheduled":       "ops",
    "followup.sent":            "ops",
    "alert.urgent":             "ops",
    "alert.ia_detected":        "ops",
    "billing.alert":            "revenue",
    "tenant.quota_exhausted":   "revenue",
    "policy.violation":         "security",
}


@dataclass
class SeverityContext:
    """
    Contexto adicional que el orquestador/servicio provee para calcular
    la severidad dinámica. Todos los campos son opcionales.
    """
    is_vip_customer: bool = False           # Cliente VIP → escala +1 nivel
    sla_deadline: Optional[datetime] = None  # Si está vencido → escala a high mínimo
    payment_amount: Optional[float] = None  # Pagos grandes → critical
    failure_count: int = 0                  # Reintentos/fallos acumulados → escala
    hours_without_response: Optional[float] = None  # Sin respuesta → escala
    is_first_interaction: bool = False      # Primera vez del cliente → medium mínimo
    customer_tags: List[str] = field(default_factory=list)  # Tags del cliente (ej: ["vip", "enterprise"])


class SeverityEngine:
    """
    Motor de cálculo automático de severidad operacional.

    Uso:
        severity, impact = SeverityEngine.calculate(
            event_type="payment.failed",
            payload={"amount": 500.00},
            context=SeverityContext(is_vip_customer=True)
        )
    """

    @staticmethod
    def calculate(
        event_type: str,
        payload: Dict[str, Any] = None,
        context: Optional[SeverityContext] = None,
    ) -> Tuple[str, Optional[str], int, List[str]]:
        """
        Retorna (severity, business_impact, priority_score, tags) calculados automáticamente.
        La severidad máxima entre base y modificadores contextuales gana.
        """
        payload = payload or {}
        context = context or SeverityContext()

        # 1. Severidad base del type de evento
        base = BASE_SEVERITY_RULES.get(event_type, "low")
        effective = base

        # 2. Modificadores contextuales (escalada sin degradar)
        effective = _max_sev(effective, SeverityEngine._apply_context(event_type, payload, context))

        # 3. Business impact canónico
        impact = BUSINESS_IMPACT_MAP.get(event_type)

        # 4. Priority Score numérico (0-100)
        score = SeverityEngine.compute_priority_score(effective, event_type, payload, context)

        # 5. Tags auto-generados
        tags = SeverityEngine.auto_tags(event_type, payload, context)

        return effective, impact, score, tags

    @staticmethod
    def _apply_context(
        event_type: str,
        payload: Dict[str, Any],
        ctx: SeverityContext,
    ) -> str:
        """Calcula el modificador de contexto (siempre devuelve >= la base)."""
        effective = "low"

        # Cliente VIP → mínimo "high"
        if ctx.is_vip_customer:
            effective = _max_sev(effective, "high")

        # SLA vencido → mínimo "high"
        if ctx.sla_deadline:
            now = datetime.now(tz=timezone.utc)
            sla = ctx.sla_deadline
            if sla.tzinfo is None:
                sla = sla.replace(tzinfo=timezone.utc)
            if now > sla:
                effective = _max_sev(effective, "high")

        # Pago grande (>$500) → critical
        amount = payload.get("amount") or payload.get("total") or ctx.payment_amount
        if amount and float(amount) >= 500:
            if event_type in ("payment.failed", "payment.completed", "order.created"):
                effective = _max_sev(effective, "critical")

        # Reintentos acumulados (>=3) → high
        if ctx.failure_count >= 3:
            effective = _max_sev(effective, "high")

        # Sin respuesta en >24h → high
        if ctx.hours_without_response and ctx.hours_without_response >= 24:
            effective = _max_sev(effective, "high")

        # Primera interacción de un cliente → asegurar visibilidad mínima
        if ctx.is_first_interaction:
            effective = _max_sev(effective, "medium")

        return effective

    @staticmethod
    def escalate_if_overdue(
        current_severity: str,
        event_type: str,
        occurred_at: datetime,
        sla_hours: int = 24,
    ) -> str:
        """
        Escala la severidad de un evento existente si ha pasado demasiado tiempo
        sin atención. Llámalo desde el health engine para eventos activos.
        """
        now = datetime.now(tz=timezone.utc)
        occ = occurred_at
        if occ.tzinfo is None:
            occ = occ.replace(tzinfo=timezone.utc)

        hours_elapsed = (now - occ).total_seconds() / 3600

        if hours_elapsed > sla_hours and _rank(current_severity) < _rank("high"):
            return "high"
        if hours_elapsed > sla_hours * 2 and _rank(current_severity) < _rank("critical"):
            return "critical"

        return current_severity

    @staticmethod
    def compute_priority_score(
        severity: str,
        event_type: str,
        payload: Dict[str, Any],
        context: Optional[SeverityContext] = None,
    ) -> int:
        """
        Calcula un score numérico 0-100 para ordenar eventos en queues y Copilot.
        Score continuo > categorías para ranking, sorting y AI.

        Base por severity:
          critical=70, high=50, medium=30, low=10
        Modificadores (+):
          VIP customer:       +15
          SLA vencido:        +10
          Pago grande (>500): +10
          Fallos acumulados:  +5 por fallo (max +15)
          Sin respuesta 24h+: +10
          Primera interaccón: +5
        """
        context = context or SeverityContext()

        BASE_SCORES = {"critical": 70, "high": 50, "medium": 30, "low": 10}
        score = BASE_SCORES.get(severity, 10)

        if context.is_vip_customer:
            score += 15

        if context.sla_deadline:
            now = datetime.now(tz=timezone.utc)
            sla = context.sla_deadline
            if sla.tzinfo is None:
                sla = sla.replace(tzinfo=timezone.utc)
            if now > sla:
                score += 10

        amount = payload.get("amount") or payload.get("total") or context.payment_amount
        if amount and float(amount) >= 500:
            score += 10

        if context.failure_count > 0:
            score += min(context.failure_count * 5, 15)

        if context.hours_without_response and context.hours_without_response >= 24:
            score += 10

        if context.is_first_interaction:
            score += 5

        return min(score, 100)  # Clamped a 100

    @staticmethod
    def auto_tags(
        event_type: str,
        payload: Dict[str, Any],
        context: Optional[SeverityContext] = None,
    ) -> List[str]:
        """
        Genera tags automáticos basados en el type de evento y contexto.
        Los tags permiten filtrar, buscar y disparar automations.

        Tags generados automáticamente:
          - Tipo de negocio: "payment", "booking", "quote", "lead", etc.
          - Riesgo: "sla-risk", "payment-fail", "overdue"
          - Cliente: "vip", "first-time"
          - Monto: "high-value" (>500)
        """
        context = context or SeverityContext()
        tags: List[str] = []

        # Tag de categoría del evento
        CATEGORY_TAGS = {
            "payment": ["payment.completed", "payment.failed"],
            "booking": ["booking.confirmed", "booking.cancelled"],
            "quote":   ["quote.generated", "quote.accepted"],
            "lead":    ["lead.created", "lead.qualified"],
            "order":   ["order.created"],
            "handoff": ["handoff.requested", "handoff.completed"],
            "followup":["followup.scheduled", "followup.sent"],
            "message": ["message.received", "message.sent"],
            "alert":   ["alert.urgent", "alert.ia_detected"],
        }
        for tag, types in CATEGORY_TAGS.items():
            if event_type in types:
                tags.append(tag)
                break

        # Tags de riesgo
        if event_type == "payment.failed":
            tags.append("payment-fail")

        if context.sla_deadline:
            now = datetime.now(tz=timezone.utc)
            sla = context.sla_deadline
            if sla.tzinfo is None:
                sla = sla.replace(tzinfo=timezone.utc)
            if now > sla:
                tags.append("sla-risk")

        if context.hours_without_response and context.hours_without_response >= 24:
            tags.append("overdue")

        # Tags de cliente
        if context.is_vip_customer:
            tags.append("vip")

        if context.is_first_interaction:
            tags.append("first-time")

        # Tags de monto
        amount = payload.get("amount") or payload.get("total")
        if amount and float(amount) >= 500:
            tags.append("high-value")

        # Tags custom del cliente (pasados desde el contexto)
        if hasattr(context, "customer_tags"):
            tags.extend(context.customer_tags)

        return list(dict.fromkeys(tags))  # Deduplicar preservando sort_order
