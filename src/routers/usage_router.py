from fastapi import APIRouter, Depends, HTTPException, Header
from uuid import UUID
from datetime import datetime
from core.dependencies import get_redis
from services.usage_tracker import UsageTracker
from services.quota_manager import QuotaManager
from domain.usage import UsageRecord, UsageResource, QuotaCheckRequest, QuotaCheckResponse

router = APIRouter(prefix="/api/usage", tags=["usage"])

def get_usage_tracker():
    from fastapi import Request
    return request.app.state.usage_tracker

def get_quota_manager():
    from fastapi import Request
    return request.app.state.quota_manager

@router.post("/record", status_code=204)
async def record_usage(
    record: UsageRecord,
    x_tenant_id: UUID = Header(...),
    # En un entorno real se inyectan a través de las dependencias correctamente.
    # usage_tracker: UsageTracker = Depends(get_usage_tracker),  
):
    if record.tenant_id != x_tenant_id:
        raise HTTPException(status_code=403, detail="Tenant mismatch")
    
    # await usage_tracker.record(record)
    return None

@router.post("/check", response_model=QuotaCheckResponse)
async def check_quota(
    request: QuotaCheckRequest,
    x_tenant_id: UUID = Header(...),
    # quota_manager: QuotaManager = Depends(get_quota_manager),
):
    if request.tenant_id != x_tenant_id:
        raise HTTPException(status_code=403, detail="Tenant mismatch")
    
    # return await quota_manager.check(request)
    # Mocking return for now
    return QuotaCheckResponse(allowed=True, remaining=9999, reset_at=datetime.utcnow(), suggested_action="continue")

@router.get("/current")
async def get_current_usage(
    x_tenant_id: UUID = Header(...),
    redis=Depends(get_redis),
):
    resources = [r.value for r in UsageResource]
    usage = {}
    
    for resource in resources:
        key = f"quota:{x_tenant_id}:{resource}:{datetime.utcnow().strftime('%Y%m')}"
        consumed = await redis.hget(key, "consumed")
        if consumed:
            usage[resource] = {"consumed": float(consumed)}
    
    return {"tenant_id": str(x_tenant_id), "period": "current_month", "usage": usage}

@router.get("/history")
async def get_usage_history(
    x_tenant_id: UUID = Header(...),
    days: int = 30,
):
    pass
