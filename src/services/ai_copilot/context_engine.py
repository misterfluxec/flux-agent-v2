import logging
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
import hashlib
import json

from services.business_memory.semantic_summary_engine import SemanticSummaryEngine
from services.business_memory.anomaly_detector import AnomalyDetector
from services.ai_copilot.safety_guardrails import SafetyGuardrails

logger = logging.getLogger(__name__)

class ContextEngine:
    """
    Fase 4C — Sprint 4C.1: AI Context Engine.
    
    Transforma la memoria operacional en contexto 'AI-ready'.
    Integra budgeting de contexto y cálculo de proveniencia de la confianza.
    """

    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.semantic_engine = SemanticSummaryEngine(db, tenant_id)
        self.anomaly_detector = AnomalyDetector(db, tenant_id)

    async def build_tenant_context(self) -> Dict[str, Any]:
        """Construye el contexto operacional completo del negocio."""
        # 1. Fetch memory sources
        tenant_summary = await self.semantic_engine.generate_tenant_summary("24h")
        operational_narrative = await self.semantic_engine.generate_operational_narrative()
        active_anomalies = await self.anomaly_detector.detect_all()

        # 2. Calculate Confidence Provenance
        # Aquí determinamos qué tan confiable es el contexto sumando las confianzas parciales
        base_confidence = tenant_summary.get("confidence", 0.90)
        narrative_conf = operational_narrative.get("confidence", 0.85)
        
        # Si hay anomalías, su peso reduce ligeramente la completitud esperada
        # (simulación de un motor de provenance real)
        memory_completeness = 0.95
        event_consistency = min(base_confidence, narrative_conf)
        anomaly_overlap = 0.90 if len(active_anomalies) > 0 else 1.0

        overall_confidence = round((memory_completeness + event_consistency + anomaly_overlap) / 3.0, 2)

        # 3. Assemble the raw Context Package
        context_package = {
            "context_version": "v1",
            "tenant_id": self.tenant_id,
            "tenant_summary": tenant_summary.get("summary", ""),
            "operational_narrative": operational_narrative.get("narrative", ""),
            "active_anomalies": active_anomalies,
            "sources_used": [
                "tenant_memory_snapshots:24h",
                "semantic_summary_engine:narrative",
                "anomaly_detector:realtime"
            ],
            "context_confidence": overall_confidence,
            "confidence_breakdown": {
                "memory_completeness": memory_completeness,
                "event_consistency": event_consistency,
                "anomaly_overlap": anomaly_overlap
            },
            "pii_redacted": True, # Forzado por diseño, no enviamos PII al tenant context
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Generar Hashes de Lineage
        context_str = json.dumps(context_package, sort_keys=True)
        context_package["context_hash"] = hashlib.sha256(context_str.encode()).hexdigest()
        
        # En una app real iteraríamos las fuentes para extraer timestamps o IDs
        derived_chain_str = f"tenant_{self.tenant_id}_" + "_".join(context_package["sources_used"])
        context_package["derived_chain_hash"] = hashlib.sha256(derived_chain_str.encode()).hexdigest()

        # 4. Apply Safety Guardrails (Budgeting, Thresholds)
        safe_context = SafetyGuardrails.validate_context(context_package)
        
        return safe_context

    async def build_incident_context(self, correlation_id: str) -> Dict[str, Any]:
        """Construye el contexto específico de un incidente (correlation_id)."""
        incident_summary = await self.semantic_engine.generate_incident_summary(correlation_id)
        
        # Provenance simple para incidentes
        event_count = incident_summary.get("event_count", 0)
        overall_confidence = 0.95 if event_count > 0 else 0.50

        context_package = {
            "context_version": "v1",
            "tenant_id": self.tenant_id,
            "correlation_id": correlation_id,
            "incident_timeline": incident_summary.get("timeline_narrative", ""),
            "event_count": event_count,
            "sources_used": ["operational_event_store:timeline"],
            "context_confidence": overall_confidence,
            "confidence_breakdown": {
                "memory_completeness": 1.0 if event_count > 0 else 0.0,
                "event_consistency": 0.90,
                "anomaly_overlap": 1.0
            },
            "pii_redacted": True, # Asumimos que SemanticEngine ya redactó
            "generated_at": datetime.now(timezone.utc).isoformat()
        }

        # Generar Hashes de Lineage
        context_str = json.dumps(context_package, sort_keys=True)
        context_package["context_hash"] = hashlib.sha256(context_str.encode()).hexdigest()
        
        derived_chain_str = f"incident_{correlation_id}_" + "_".join(context_package["sources_used"])
        context_package["derived_chain_hash"] = hashlib.sha256(derived_chain_str.encode()).hexdigest()

        safe_context = SafetyGuardrails.validate_context(context_package)
        return safe_context
