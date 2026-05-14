from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum
from typing import Optional

class ReplaySource(str, Enum):
    FROM_RAW = "from_raw"
    FROM_ENVELOPE = "from_envelope"
    FROM_EVENTBUS = "from_eventbus"

class ReplayManifest(BaseModel):
    """
    Historical record of a replay operation (Sprint B.2).
    Gobernanza operacional: Quién, por qué y qué se reprocesó.
    """
    replay_id: UUID = Field(default_factory=uuid4)
    initiated_by: str # user_id or 'system'
    source: ReplaySource
    reason: str
    
    event_count: int
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    replay_version: str = "1.0"
    status: str = "running" # running, completed, failed
    
    # Metadata
    tenant_id: Optional[UUID] = None
    filter_criteria: Optional[dict] = None
