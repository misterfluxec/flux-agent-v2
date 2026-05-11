from enum import Enum
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

class FailureType(str, Enum):
    TRANSIENT      = "transient"       # Network / timeout — retryable
    PERMANENT      = "permanent"       # Logic failure — human action required
    SECURITY       = "security"        # Invalid signature / fraud
    RATE_LIMIT     = "rate_limit"      # External saturation
    DATA_CONFLICT  = "data_conflict"   # Drift / concurrency
    SCHEMA_CHANGE  = "schema_change"   # ERP/source altered

class OperationalDomain(str, Enum):
    COMMERCE    = "commerce"
    INVENTORY   = "inventory"
    PAYMENTS    = "payments"
    CONNECTORS  = "connectors"
    OPERATIONS  = "operations"
    AI          = "ai"

class VisibilityScope(str, Enum):
    PUBLIC   = "public"    # Visible in all dashboards
    INTERNAL = "internal"  # Only system consoles
    AUDIT    = "audit"     # Only audit logs

class RetentionTier(str, Enum):
    HOT  = "hot"   # 7–30 days: live event_outbox
    WARM = "warm"  # 3–12 months: memory profiles
    COLD = "cold"  # Historical: future S3/Blob archival

class EventPriority(str, Enum):
    LOW      = "low"
    NORMAL   = "normal"
    HIGH     = "high"
    CRITICAL = "critical"

class RetryPolicy(str, Enum):
    NONE                = "none"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR              = "linear"
    IMMEDIATE_DLQ       = "immediate_dlq"

class RetentionPolicy(str, Enum):
    DAYS_7     = "7_days"
    DAYS_30    = "30_days"
    YEARS_1    = "1_year"
    INDEFINITE = "indefinite"

class PiiClassification(str, Enum):
    PUBLIC       = "public"
    INTERNAL     = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED   = "restricted"

class OperationalSeverity(str, Enum):
    INFO    = "info"
    WARNING = "warning"
    ERROR   = "error"
    FATAL   = "fatal"

class EventDefinition(BaseModel):
    """
    Definición estricta de un Evento en el sistema.
    Ningún evento puede ser publicado si no existe en este registro.
    """
    event_name: str
    version: str
    description: str
    domain: OperationalDomain = OperationalDomain.OPERATIONS
    priority: EventPriority = EventPriority.NORMAL
    replay_strategy: RetryPolicy = RetryPolicy.EXPONENTIAL_BACKOFF
    retention_policy: RetentionPolicy = RetentionPolicy.DAYS_30
    retention_tier: RetentionTier = RetentionTier.HOT
    replayable: bool = True
    failure_type: FailureType = FailureType.TRANSIENT
    producer: str
    consumers: List[str]
    pii_classification: PiiClassification = PiiClassification.INTERNAL
    severity_default: OperationalSeverity = OperationalSeverity.INFO
    visibility_scope: VisibilityScope = VisibilityScope.INTERNAL

class EventRegistry:
    """
    Centralized Event Registry.
    La fuente de verdad para el ecosistema de eventos de FluxAgent.
    """
    
    _registry: Dict[str, EventDefinition] = {}

    @classmethod
    def register(cls, definition: EventDefinition):
        key = f"{definition.event_name}.{definition.version}"
        if key in cls._registry:
            raise ValueError(f"Event {key} is already registered.")
        cls._registry[key] = definition

    @classmethod
    def get_definition(cls, event_name: str, version: str) -> Optional[EventDefinition]:
        return cls._registry.get(f"{event_name}.{version}")


# ==========================================
# CORE EVENTS BOOTSTRAP (Registration)
# ==========================================

# Payment Events
EventRegistry.register(EventDefinition(
    event_name="payment.completed",
    version="v1",
    description="Emitido cuando un pago es conciliado y exitoso.",
    domain=OperationalDomain.PAYMENTS,
    priority=EventPriority.HIGH,
    replay_strategy=RetryPolicy.EXPONENTIAL_BACKOFF,
    retention_policy=RetentionPolicy.YEARS_1,
    retention_tier=RetentionTier.WARM,
    replayable=True,
    failure_type=FailureType.TRANSIENT,
    producer="payment_reconciliation_engine",
    consumers=["inventory_engine", "customer_timeline_aggregator", "order_lifecycle", "memory_aggregator"],
    pii_classification=PiiClassification.CONFIDENTIAL,
    severity_default=OperationalSeverity.INFO,
    visibility_scope=VisibilityScope.INTERNAL
))

EventRegistry.register(EventDefinition(
    event_name="payment.failed",
    version="v1",
    description="Emitido cuando un intento de pago es rechazado.",
    domain=OperationalDomain.PAYMENTS,
    priority=EventPriority.HIGH,
    failure_type=FailureType.PERMANENT,
    producer="payment_reconciliation_engine",
    consumers=["customer_timeline_aggregator", "memory_aggregator"],
    pii_classification=PiiClassification.INTERNAL,
    severity_default=OperationalSeverity.WARNING
))

# Inventory Events
EventRegistry.register(EventDefinition(
    event_name="inventory.drift_detected",
    version="v1",
    description="ALARMA: Discrepancia detectada entre Snapshot y Ledger inmutable.",
    domain=OperationalDomain.INVENTORY,
    priority=EventPriority.CRITICAL,
    replay_strategy=RetryPolicy.EXPONENTIAL_BACKOFF,
    retention_policy=RetentionPolicy.INDEFINITE,
    retention_tier=RetentionTier.COLD,
    replayable=True,
    failure_type=FailureType.DATA_CONFLICT,
    producer="inventory_integrity_validator",
    consumers=["alert_manager", "customer_timeline_aggregator", "memory_aggregator"],
    pii_classification=PiiClassification.INTERNAL,
    severity_default=OperationalSeverity.FATAL,
    visibility_scope=VisibilityScope.PUBLIC
))

EventRegistry.register(EventDefinition(
    event_name="inventory.reserved",
    version="v1",
    description="Soft lock de inventario (ej. Carrito).",
    domain=OperationalDomain.INVENTORY,
    priority=EventPriority.NORMAL,
    replayable=True,
    failure_type=FailureType.TRANSIENT,
    producer="reservation_engine",
    consumers=["inventory_engine", "memory_aggregator"],
    pii_classification=PiiClassification.INTERNAL,
    severity_default=OperationalSeverity.INFO
))

# Connector Events
EventRegistry.register(EventDefinition(
    event_name="connector.schema_changed",
    version="v1",
    description="El origen de datos (ERP/Excel) cambió sus columnas inesperadamente.",
    domain=OperationalDomain.CONNECTORS,
    priority=EventPriority.CRITICAL,
    replay_strategy=RetryPolicy.IMMEDIATE_DLQ,
    retention_policy=RetentionPolicy.YEARS_1,
    retention_tier=RetentionTier.WARM,
    replayable=False,  # Requiere intervención humana, no replay automático
    failure_type=FailureType.SCHEMA_CHANGE,
    producer="connector_sync_worker",
    consumers=["alert_manager", "sync_engine", "memory_aggregator"],
    pii_classification=PiiClassification.INTERNAL,
    severity_default=OperationalSeverity.ERROR,
    visibility_scope=VisibilityScope.PUBLIC
))

# Human-in-the-Loop (HITL) Action Events
EventRegistry.register(EventDefinition(
    event_name="action.proposed",
    version="v1",
    description="Una acción sugerida por IA o humano, pendiente de aprobación HITL.",
    domain=OperationalDomain.OPERATIONS,
    priority=EventPriority.NORMAL,
    replayable=False,
    failure_type=FailureType.TRANSIENT,
    producer="ai_copilot_engine",
    consumers=["hitl_engine", "memory_aggregator"],
    pii_classification=PiiClassification.INTERNAL,
    severity_default=OperationalSeverity.INFO
))

EventRegistry.register(EventDefinition(
    event_name="action.approved",
    version="v1",
    description="Acción validada por un humano y aprobada por el Action Governance Layer.",
    domain=OperationalDomain.OPERATIONS,
    priority=EventPriority.HIGH,
    replayable=False,
    failure_type=FailureType.TRANSIENT,
    producer="hitl_engine",
    consumers=["execution_engine", "memory_aggregator", "audit_logger"],
    pii_classification=PiiClassification.INTERNAL,
    severity_default=OperationalSeverity.INFO
))

EventRegistry.register(EventDefinition(
    event_name="action.executed",
    version="v1",
    description="Acción operacional ejecutada exitosamente en el backend.",
    domain=OperationalDomain.OPERATIONS,
    priority=EventPriority.HIGH,
    replayable=False,
    failure_type=FailureType.TRANSIENT,
    producer="execution_engine",
    consumers=["memory_aggregator", "customer_timeline_aggregator"],
    pii_classification=PiiClassification.INTERNAL,
    severity_default=OperationalSeverity.INFO
))

EventRegistry.register(EventDefinition(
    event_name="action.rejected",
    version="v1",
    description="Acción rechazada (por el humano o por fallar la Gobernanza).",
    domain=OperationalDomain.OPERATIONS,
    priority=EventPriority.NORMAL,
    replayable=False,
    failure_type=FailureType.SECURITY,
    producer="hitl_engine",
    consumers=["memory_aggregator"],
    pii_classification=PiiClassification.INTERNAL,
    severity_default=OperationalSeverity.WARNING
))
