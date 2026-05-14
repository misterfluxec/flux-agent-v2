from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from uuid import UUID, uuid4

class CanonicalCustomer(BaseModel):
    """Unified Customer model for FluxAgent (Anti-Corruption Layer)"""
    external_id: str
    source: str  # 'meta', 'shopify', 'evolution', etc.
    email: Optional[str] = None
    phone: Optional[str] = None
    name: Optional[str] = None
    country_code: str = "EC"
    metadata: Dict[str, Any] = Field(default_factory=dict)

class CanonicalMessage(BaseModel):
    """Unified Message model across all channels"""
    external_id: str
    channel: str
    sender_id: str
    content: str
    timestamp: float
    metadata: Dict[str, Any] = Field(default_factory=dict)

class CanonicalOrder(BaseModel):
    """Unified Order model across ERPs and E-commerce"""
    external_id: str
    provider: str
    customer_id: str
    total_amount: float
    currency: str = "USD"
    items: list[Dict[str, Any]] = Field(default_factory=list)
    status: str

class ProcessingState(str, Enum):
    RECEIVED = "received"
    DEDUPED = "deduped"
    NORMALIZED = "normalized"
    PUBLISHED = "published"
    FAILED = "failed"
    QUARANTINED = "quarantined"

class CanonicalEnvelope(BaseModel):
    """Universal wrapper for all external provider events (Fortress Path)"""
    provider: str
    provider_event_id: str
    tenant_id: UUID
    correlation_id: str
    received_at: float # Timestamp
    payload_version: str = "1.0"
    country_code: str
    actor_type: str = "user" # user, system, bot
    raw_reference_id: str # ID in incoming_provider_payloads
    
    # State tracking
    processing_state: ProcessingState = ProcessingState.RECEIVED
    
    # Latency tracking (Timestamps)
    normalized_at: float | None = None
    published_at: float | None = None
    failed_at: float | None = None
    
    # Checksum for early deduplication
    dedup_hash: str
    dedup_expires_at: float | None = None



