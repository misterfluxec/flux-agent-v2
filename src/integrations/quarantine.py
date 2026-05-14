from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID, uuid4
from typing import Dict, Any
from enum import Enum

class QuarantineReason(str, Enum):
    SCHEMA_INVALID = "schema_invalid"
    MISSING_FIELDS = "missing_fields"
    UNKNOWN_VERSION = "unknown_version"
    CORRUPT_PAYLOAD = "corrupt_payload"
    SECURITY_VIOLATION = "security_violation"

class QuarantinedEvent(BaseModel):
    """
    Registry for malformed or schema-broken payloads (Sprint B.2).
    v2.5: Clasificación por reason_code para gobernanza operativa.
    """
    id: UUID = Field(default_factory=uuid4)
    provider: str
    raw_payload: Dict[str, Any]
    
    reason_code: QuarantineReason
    reason_detail: str
    
    quarantined_at: datetime = Field(default_factory=datetime.utcnow)
    tenant_id: UUID | None = None
    
    # Traceability
    correlation_id: str | None = None
    schema_fingerprint: str | None = None
