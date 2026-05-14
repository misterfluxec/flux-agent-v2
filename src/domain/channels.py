from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime

class ChannelStatus(str, Enum):
    DISCONNECTED = "disconnected"
    AWAITING_QR_SCAN = "awaiting_qr_scan"
    PENDING_CONFIGURATION = "pending_configuration"
    VALIDATING = "validating"
    CONNECTED = "connected"
    DEGRADED = "degraded"
    RATE_LIMITED = "rate_limited"
    RECONNECTING = "reconnecting"
    ERROR = "error"
    SUSPENDED = "suspended"

class ChannelConfig(BaseModel):
    id: UUID
    tenant_id: UUID
    channel_type: str
    status: ChannelStatus
    external_session_id: Optional[str] = None
    config: Dict[str, Any] = Field(default_factory=dict)
    health_score: int = 100
    last_heartbeat: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class ChannelConnectionRequest(BaseModel):
    config: Dict[str, Any] = Field(default_factory=dict)
