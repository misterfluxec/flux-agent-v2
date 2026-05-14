from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID, uuid4
from typing import Dict, Any

class IncomingProviderPayload(BaseModel):
    """
    Inmutable record of an incoming webhook/payload from an external provider.
    v2.5: Added schema_fingerprint for drift detection.
    """
    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    provider: str 
    provider_event_id: str 
    
    # Original data
    payload: Dict[str, Any] 
    payload_compressed: bytes | None = None 
    compression_type: str | None = None 
    
    checksum: str # SHA256 of original payload
    schema_fingerprint: str | None = None # Hash of keys structure for drift detection
    
    received_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Metadata for processing
    processed: bool = False
    processing_attempts: int = 0
    error_log: str | None = None
    quarantined: bool = False 
