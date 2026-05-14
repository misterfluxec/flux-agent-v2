import uuid
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
from domain.integration_lifecycle import SyncStatus

class IntegrationSyncRun(BaseModel):
    """
    Registro histórico de una ejecución de sincronización.
    Mantiene la trazabilidad y observabilidad del Connector Engine.
    """
    sync_id: str = Field(default_factory=lambda: f"sync_{uuid.uuid4().hex[:12]}")
    session_id: str = Field(..., description="ID de la integración/sesión origen")
    correlation_id: str = Field(..., description="ID de correlación para Distributed Tracing")
    
    status: SyncStatus = Field(default=SyncStatus.SYNCING)
    
    rows_processed: int = Field(default=0)
    rows_failed: int = Field(default=0)
    
    started_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = None
    
    error_message: Optional[str] = Field(default=None, description="Razón de fallo si status es FAILED o DEGRADED")

    def mark_completed(self):
        self.status = SyncStatus.IDLE
        self.finished_at = datetime.utcnow()

    def mark_degraded(self, error: str):
        self.status = SyncStatus.DEGRADED
        self.error_message = error
        self.finished_at = datetime.utcnow()
        
    def mark_failed(self, error: str):
        self.status = SyncStatus.BROKEN_MAPPING # or FAILED
        self.error_message = error
        self.finished_at = datetime.utcnow()
