import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from database import obtener_sesion_con_rls
from domain.integration_lifecycle import IntegrationLifecycleEngine, ConnectorSessionStatus
from core.security.secrets_vault import SecretsVault
from services.discovery_worker import run_discovery_task

router = APIRouter(prefix="/api/v1/integrations", tags=["Integrations V2"])
logger = logging.getLogger(__name__)

# En una app real esto sería inyectado
lifecycle_engine = IntegrationLifecycleEngine()

@router.post("/sessions")
async def create_connector_session(
    payload: Dict[str, Any],
    # db: AsyncSession = Depends(obtener_sesion_con_rls) # Fake DI for now to get tenant_id, assume tenant_id passed in payload for testing
):
    """Paso 1: Iniciar una sesión de conector."""
    tenant_id = payload.get("tenant_id", "demo-tenant-id")
    provider = payload.get("provider")
    
    if not provider:
        raise HTTPException(status_code=400, detail="Provider is required")
        
    session = lifecycle_engine.create_session(tenant_id, provider)
    return {"session_id": session.session_id, "status": session.status.value, "provider": provider}

@router.post("/sessions/{session_id}/test")
async def test_connection(
    session_id: str,
    payload: Dict[str, Any]
):
    """Paso 2: Validar credenciales (Test Connection)."""
    tenant_id = payload.get("tenant_id", "demo-tenant-id")
    raw_credentials = payload.get("credentials")
    
    if not raw_credentials:
        raise HTTPException(status_code=400, detail="Credentials are required")
        
    try:
        # Encriptar y obtener ID de referencia seguro
        secret_ref = SecretsVault.store_credentials(tenant_id, "sqlserver", raw_credentials)
        session = lifecycle_engine.start_test_connection(session_id, secret_ref.credential_id)
        
        # Aquí probaríamos la conexión real. Para el MVP simulamos éxito.
        # ... connector.test_connection(secret_ref) ...
        
        return {"status": session.status.value, "message": "Conexión exitosa"}
    except Exception as e:
        lifecycle_engine.transition_to(session_id, ConnectorSessionStatus.FAILED, str(e))
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/sessions/{session_id}/discover")
async def start_discovery(
    session_id: str,
    background_tasks: BackgroundTasks
):
    """Paso 3: Disparar el descubrimiento asíncrono del esquema."""
    try:
        session = lifecycle_engine.complete_test_and_start_discovery(session_id)
        
        # Despachar trabajo asíncrono
        background_tasks.add_task(run_discovery_task, session_id, lifecycle_engine)
        
        return {"status": session.status.value, "message": "Discovery started in background"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/sessions/{session_id}")
async def get_session_status(session_id: str):
    """Polling: Revisar el status del discovery o sesión."""
    session = lifecycle_engine.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    response = {
        "session_id": session.session_id,
        "status": session.status.value,
        "provider": session.provider
    }
    
    if session.status == ConnectorSessionStatus.MAPPING:
        response["discovered_schema"] = session.discovered_schema
        
    if session.error_message:
        response["error"] = session.error_message
        
    return response
