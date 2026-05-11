from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import json
import hashlib
import logging
from typing import Dict, Any, Optional, Set

logger = logging.getLogger(__name__)


# =============================================================================
# WHITELIST DE OVERRIDES PERMITIDOS POR NIVEL
# Garantiza que un agente individual NO puede romper políticas del tenant.
# =============================================================================

# Solo estos campos de personality pueden ser sobreescritos a nivel de agente.
ALLOWED_PERSONALITY_OVERRIDES: Set[str] = {
    "verbosity",
    "emoji_usage",
    "response_speed",
    "greeting_style",
    "tone",  # Tono permitido: el agente puede variar cómo habla, no qué vende
}

# Los agentes NUNCA pueden tocar estos campos de strategy (son responsabilidad del tenant).
PROTECTED_STRATEGY_FIELDS: Set[str] = {
    "sla_rules",
    "compliance_rules",
    "pricing_rules",
    "discount_policy",
    "legal_disclaimers",
    "workflows",          # Los workflows son de nivel tenant, no de agente
}


def _compute_config_hash(personality: dict, commercial_strategy: dict, workflows: list) -> str:
    """
    Genera SHA-256 del config actual del playbook.
    Permite detectar drift, invalidar cache, hacer A/B testing y rollback seguro.
    """
    canonical = json.dumps(
        {"personality": personality, "commercial_strategy": commercial_strategy, "workflows": sorted(workflows)},
        sort_keys=True,
        ensure_ascii=False
    )
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]  # 16 chars suficientes para identificación


class CommercialPlaybookService:
    """
    Servicio para gestionar Commercial Playbooks.

    Arquitectura de 3 niveles:
      1. System Template  → Templates globales por industria (código)
      2. Tenant Playbook  → Personalización del negocio (DB, con config_hash)
      3. Agent Overrides  → Micro-personalidad individual (whitelist estricta)

    El orquestador NO recibe el playbook completo.
    En su lugar, usa get_contextual_strategy() para inyectar SOLO lo relevante
    a la situación actual (menos tokens, menos alucinación, más control).
    """

    SYSTEM_TEMPLATES = {
        "retail": {
            "name": "Retail & E-commerce",
            "personality": {
                "tone": "dinámico",
                "verbosity": "medium",
                "urgency_style": "high",
                "emoji_usage": "medium",
                "greeting_style": "casual"
            },
            "commercial_strategy": {
                "focus": "conversión",
                "upsell_style": "sugerido",
                "closing_style": "direct",
                "objection_rules": {
                    "price": "Destaca valor + envío gratis en pedidos +$50",
                    "competitor": "Ofrece garantía extendida + soporte 24/7",
                    "quality": "Comparte reseñas + política de devolución 30 días"
                },
                "urgency_triggers": ["stock limitado", "oferta por tiempo limitado", "envío gratis hoy"]
            },
            "workflows": ["cart_recovery_2h", "low_stock_urgency", "post_purchase_survey"],
            "sla_rules": {"first_response_sec": 30, "quote_valid_hours": 48},
            "kpi_targets": {"conversion_pct": 15, "aov_increase_pct": 10}
        },
        "clinic": {
            "name": "Salud & Bienestar",
            "personality": {
                "tone": "empático",
                "verbosity": "low",
                "urgency_style": "prioritario",
                "emoji_usage": "low",
                "greeting_style": "formal"
            },
            "commercial_strategy": {
                "focus": "salud",
                "urgency_handling": "priorizar",
                "closing_style": "consultative",
                "objection_rules": {
                    "price": "Ofrece planes de pago / enfatiza diagnóstico temprano",
                    "availability": "Lista de espera activa + notificación de cancelación",
                    "urgency": "Sugiere consulta virtual inmediata"
                },
                "urgency_triggers": ["síntoma severo", "urgencia declarada", "paciente sin cita previa"]
            },
            "workflows": ["appointment_reminder_24h", "no_show_followup", "patient_feedback_48h"],
            "sla_rules": {"booking_confirmation_min": 10, "urgent_response_sec": 60},
            "kpi_targets": {"show_rate_pct": 85, "retention_mo": 90}
        },
        "services": {
            "name": "Servicios Profesionales",
            "personality": {
                "tone": "consultivo",
                "verbosity": "high",
                "urgency_style": "soft",
                "emoji_usage": "minimal",
                "greeting_style": "profesional"
            },
            "commercial_strategy": {
                "focus": "confianza",
                "scope_clarity": "alta",
                "closing_style": "consultative",
                "objection_rules": {
                    "scope": "Define entregables claros + fases aprobables",
                    "timeline": "Ofrece prioridad con recargo o fase inicial gratuita",
                    "price": "Presenta ROI proyectado + testimonios de clientes"
                },
                "urgency_triggers": ["deadline específico", "presupuesto limitado", "necesidad inmediata"]
            },
            "workflows": ["quote_followup_48h", "project_milestone_update", "invoice_reminder"],
            "sla_rules": {"proposal_delivery_hours": 24, "revision_rounds": 2},
            "kpi_targets": {"close_rate_pct": 40, "scope_creep_pct": 5}
        }
    }

    @staticmethod
    async def get_or_create_playbook(
        tenant_id: str,
        industry: str,
        db: AsyncSession,
        use_system_template: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Obtiene playbook activo del tenant o lo crea desde template del sistema."""

        result = await db.execute(text("""
            SELECT id, industry, version, name, personality, commercial_strategy,
                   workflows, sla_rules, kpi_targets, config_hash
            FROM commercial_playbooks
            WHERE tenant_id = :tenant_id AND industry = :industry AND is_active = true
            ORDER BY version DESC
            LIMIT 1
        """), {"tenant_id": tenant_id, "industry": industry})

        playbook = result.fetchone()
        if playbook:
            return dict(playbook._mapping)

        if use_system_template and industry in CommercialPlaybookService.SYSTEM_TEMPLATES:
            template = CommercialPlaybookService.SYSTEM_TEMPLATES[industry]
            config_hash = _compute_config_hash(
                template["personality"],
                template["commercial_strategy"],
                template["workflows"]
            )

            result = await db.execute(text("""
                INSERT INTO commercial_playbooks (
                    tenant_id, industry, version, name, personality, commercial_strategy,
                    workflows, sla_rules, kpi_targets, config_hash, is_system_template
                ) VALUES (
                    :tenant_id, :industry, '1.0', :name, :personality, :commercial_strategy,
                    :workflows, :sla_rules, :kpi_targets, :config_hash, false
                ) RETURNING id, industry, version, name, personality, commercial_strategy,
                             workflows, sla_rules, kpi_targets, config_hash
            """), {
                "tenant_id": tenant_id,
                "industry": industry,
                "name": template["name"],
                "personality": json.dumps(template["personality"]),
                "commercial_strategy": json.dumps(template["commercial_strategy"]),
                "workflows": json.dumps(template["workflows"]),
                "sla_rules": json.dumps(template["sla_rules"]),
                "kpi_targets": json.dumps(template["kpi_targets"]),
                "config_hash": config_hash,
            })
            await db.commit()
            new_playbook = result.fetchone()
            if new_playbook:
                return dict(new_playbook._mapping)

        return None

    @staticmethod
    def _apply_agent_overrides(base: dict, raw_overrides: dict, allowed: Set[str]) -> dict:
        """
        Aplica overrides del agente sobre un dict base usando whitelist estricta.
        Cualquier key fuera de `allowed` es ignorada silenciosamente y loggeada.
        """
        safe_overrides = {}
        rejected = []
        for key, val in raw_overrides.items():
            if key in allowed:
                safe_overrides[key] = val
            else:
                rejected.append(key)

        if rejected:
            logger.warning(f"Overrides rechazados (fuera de whitelist): {rejected}")

        return {**base, **safe_overrides}

    @staticmethod
    async def get_effective_config(agent_id: str, db: AsyncSession) -> Dict[str, Any]:
        """
        Obtiene configuración operacional efectiva para un agente.
        Aplica overrides de agente con whitelist estricta.
        Nunca retorna el playbook completo: usa get_contextual_strategy() para el LLM.
        """
        result = await db.execute(
            text("SELECT id, playbook_id, metadata FROM agentes WHERE id = :agent_id"),
            {"agent_id": agent_id}
        )
        agent = result.fetchone()

        if not agent or not agent.playbook_id:
            return {}

        result = await db.execute(text("""
            SELECT personality, commercial_strategy, workflows, sla_rules, kpi_targets, config_hash
            FROM commercial_playbooks
            WHERE id = :playbook_id
        """), {"playbook_id": agent.playbook_id})
        playbook = result.fetchone()

        if not playbook:
            return {}

        agent_metadata = agent.metadata or {}
        if isinstance(agent_metadata, str):
            try:
                agent_metadata = json.loads(agent_metadata)
            except Exception:
                agent_metadata = {}

        personality_raw_overrides = agent_metadata.get("personality_overrides", {})
        strategy_raw_overrides = agent_metadata.get("strategy_overrides", {})

        # Personality: se permite solo la whitelist
        merged_personality = CommercialPlaybookService._apply_agent_overrides(
            playbook.personality or {},
            personality_raw_overrides,
            ALLOWED_PERSONALITY_OVERRIDES
        )

        # Strategy: solo campos NO protegidos pueden ser sobreescritos
        allowed_strategy = set(playbook.commercial_strategy.keys()) - PROTECTED_STRATEGY_FIELDS
        merged_strategy = CommercialPlaybookService._apply_agent_overrides(
            playbook.commercial_strategy or {},
            strategy_raw_overrides,
            allowed_strategy
        )

        return {
            "personality": merged_personality,
            "commercial_strategy": merged_strategy,
            "workflows": playbook.workflows,         # Immutable a nivel agente
            "sla_rules": playbook.sla_rules,         # Immutable a nivel agente
            "kpi_targets": playbook.kpi_targets,
            "config_hash": playbook.config_hash,     # Para invalidar cache del orquestador
        }

    @staticmethod
    def get_contextual_strategy(full_config: Dict[str, Any], situation: str) -> Dict[str, Any]:
        """
        Extrae SOLO el contexto relevante del playbook para la situación actual.
        El orquestador inyecta esto al LLM, NO el playbook completo.

        Situaciones soportadas:
          - "price_objection"     → Regla de objeción de precio
          - "competitor_objection"→ Regla de objeción de competidor
          - "urgency"             → Triggers de urgencia
          - "closing"             → Estilo de cierre
          - "greeting"            → Tono + saludo
        """
        strategy = full_config.get("commercial_strategy", {})
        personality = full_config.get("personality", {})
        objection_rules = strategy.get("objection_rules", {})

        CONTEXT_MAP = {
            "price_objection": {
                "rule": objection_rules.get("price"),
                "tone": personality.get("tone"),
                "closing_style": strategy.get("closing_style"),
            },
            "competitor_objection": {
                "rule": objection_rules.get("competitor"),
                "tone": personality.get("tone"),
            },
            "urgency": {
                "triggers": strategy.get("urgency_triggers", []),
                "urgency_style": personality.get("urgency_style"),
            },
            "closing": {
                "closing_style": strategy.get("closing_style"),
                "upsell_style": strategy.get("upsell_style"),
                "tone": personality.get("tone"),
            },
            "greeting": {
                "greeting_style": personality.get("greeting_style"),
                "tone": personality.get("tone"),
                "emoji_usage": personality.get("emoji_usage"),
            },
        }

        context = CONTEXT_MAP.get(situation, {})
        # Eliminar valores None del contexto antes de pasarlo al LLM
        return {k: v for k, v in context.items() if v is not None}
