from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class SyncTriggerType(str, Enum):
    MANUAL = "manual"
    CRON = "cron"
    WEBHOOK = "webhook"

class SyncPolicy(BaseModel):
    """
    Política formal de sincronización.
    Controla cómo y cuándo el sistema buscará actualizaciones en este conector.
    """
    trigger: SyncTriggerType = Field(default=SyncTriggerType.MANUAL)
    cron_expression: Optional[str] = Field(default=None, description="Ej: '0 * * * *' para cada hora")
    batch_size: int = Field(default=1000, description="Límite por chunk de lectura para evitar OOM")
    max_retries: int = Field(default=3, description="Intentos ante caídas de red")
    retry_backoff_seconds: int = Field(default=60)
    dry_run: bool = Field(default=False, description="Si es True, no impacta la base de datos de producción")
    webhook_secret: Optional[str] = Field(default=None, description="Secreto para firmar y validar webhooks entrantes")

    def validate_policy(self):
        if self.trigger == SyncTriggerType.CRON and not self.cron_expression:
            raise ValueError("Cron trigger requiere cron_expression")
        if self.trigger == SyncTriggerType.WEBHOOK and not self.webhook_secret:
            raise ValueError("Webhook trigger requiere webhook_secret")
