from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from database import get_db
# Dependencias mockeadas de autenticación
def get_current_tenant_id() -> str:
    return "tnt_01hq8xx123"

def get_current_user_id() -> str:
    return "usr_99x_admin"

def get_current_user_roles() -> List[str]:
    return ["operations_admin"]

from services.operations.hitl_engine import HITLEngine

router = APIRouter(prefix="/api/v1/operations", tags=["Operations"])

class ActionExecutionRequest(BaseModel):
    payload: Dict[str, Any]
    ai_audit_log_id: str = None  # Para enlazar la decisión humana a la sugerencia IA original

@router.post("/execute/{action_name}")
def execute_governed_action(
    action_name: str,
    request: ActionExecutionRequest,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    user_id: str = Depends(get_current_user_id),
    user_roles: List[str] = Depends(get_current_user_roles)
) -> Dict[str, Any]:
    """
    Fase 5A: Ejecuta una acción operacional validada por un humano (HITL).
    Pasa por el Action Governance Layer antes de ser ejecutada.
    """
    hitl_engine = HITLEngine(db, tenant_id, user_id, user_roles)
    
    result = hitl_engine.execute_action(
        action_name=action_name.upper(),
        payload=request.payload,
        ai_audit_log_id=request.ai_audit_log_id
    )
    
    if result.get("status") == "error":
        raise HTTPException(status_code=403, detail=result.get("message"))
        
    return result
