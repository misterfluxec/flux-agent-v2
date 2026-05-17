import logging
import uuid
from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class ConnectorSessionStatus(str, Enum):
    CONFIGURING = "configuring"   # Ingresando credenciales
    TESTING = "testing"           # Validando credenciales (Test Connection)
    DISCOVERING = "discovering"   # Leyendo schema (tablas/hojas)
    MAPPING = "mapping"           # Esperando que el usuario mapee columnas
    READY = "ready"               # Listo para sync
    FAILED = "failed"             # Falló conexión o discovery

class SyncStatus(str, Enum):
    IDLE = "idle"
    SYNCING = "syncing"
    DEGRADED = "degraded"         # Fallos parciales / retries failing
    PAUSED = "paused"             # Detenido manualmente
    BROKEN_MAPPING = "broken_mapping" # Schema Drift detectado

class ConnectorSession:
    """
    Sesión de configuración de conector.
    Evita guardar integración "a medias" y aísla el flujo multi-paso.
    """
    def __init__(self, tenant_id: str, provider: str):
        self.session_id = f"sess_{uuid.uuid4().hex[:12]}"
        self.tenant_id = tenant_id
        self.provider = provider
        self.status = ConnectorSessionStatus.CONFIGURING
        self.secret_ref_id: Optional[str] = None
        self.discovered_schema: Optional[Dict[str, Any]] = None
        self.created_at = datetime.utcnow()
        self.error_message: Optional[str] = None

class IntegrationLifecycleEngine:
    """
    Controlador de status para el ciclo de vida de una integración.
    Maneja transiciones seguras entre estados (Configuración -> Discovery -> Sync).
    """
    def __init__(self):
        # En memoria para simplificar la simulación inicial, luego irá a DB o Redis.
        self._sessions: Dict[str, ConnectorSession] = {}

    def create_session(self, tenant_id: str, provider: str) -> ConnectorSession:
        session = ConnectorSession(tenant_id, provider)
        self._sessions[session.session_id] = session
        logger.info(f"[IntegrationEngine] Nueva sesión creada: {session.session_id} ({provider})")
        return session

    def get_session(self, session_id: str) -> Optional[ConnectorSession]:
        return self._sessions.get(session_id)

    def transition_to(self, session_id: str, new_status: ConnectorSessionStatus, error: Optional[str] = None) -> ConnectorSession:
        session = self.get_session(session_id)
        if not session:
            raise ValueError("Sesión no encontrada")
        
        old_status = session.status
        session.status = new_status
        session.error_message = error
        
        logger.info(f"[IntegrationEngine] Sesión {session_id}: {old_status.value} -> {new_status.value}")
        return session

    def start_test_connection(self, session_id: str, secret_ref_id: str) -> ConnectorSession:
        """
        Transición al status de prueba de credenciales.
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError("Sesión no encontrada")
        
        session.secret_ref_id = secret_ref_id
        return self.transition_to(session_id, ConnectorSessionStatus.TESTING)

    def complete_test_and_start_discovery(self, session_id: str) -> ConnectorSession:
        """
        Si la conexión fue exitosa, pasamos a descubrimiento.
        Aquí se despacharía el Job Asíncrono (EventBus).
        """
        return self.transition_to(session_id, ConnectorSessionStatus.DISCOVERING)

    def finish_discovery(self, session_id: str, schema: Dict[str, Any]) -> ConnectorSession:
        """
        El worker asíncrono llama a este método al terminar de leer las tablas/hojas.
        """
        session = self.get_session(session_id)
        if session:
            session.discovered_schema = schema
        return self.transition_to(session_id, ConnectorSessionStatus.MAPPING)

    def finalize_setup(self, session_id: str) -> ConnectorSession:
        """
        El usuario completó el mapeo y guardó la configuración.
        """
        # Aquí se insertaría en la tabla oficial de integraciones activas
        return self.transition_to(session_id, ConnectorSessionStatus.READY)
