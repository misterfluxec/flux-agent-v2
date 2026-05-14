from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime
from uuid import UUID
from enum import Enum

class HumanTaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class HumanTaskPayload(BaseModel):
    tenant_id: UUID
    title: str
    description: Optional[str] = None
    role_required: Optional[str] = None
    assigned_to: Optional[UUID] = None
    context_payload: Dict[str, Any] = Field(default_factory=dict)
    due_at: Optional[datetime] = None

class HumanTaskResolution(BaseModel):
    task_id: UUID
    resolved_by: UUID
    resolution_payload: Dict[str, Any]
    status: HumanTaskStatus = HumanTaskStatus.COMPLETED
