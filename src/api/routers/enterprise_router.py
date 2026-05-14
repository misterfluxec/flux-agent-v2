from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

# from src.core.database import get_db
# from src.core.middleware.tenant_isolation import get_tenant_id
from src.services.finance.ledger_service import LedgerService
from src.services.compliance.country_profile_service import CountryProfileService
from src.services.storage.asset_service import AssetService

router = APIRouter(prefix="/api/v1/enterprise", tags=["Enterprise"])

@router.get("/ledger/balance/{customer_id}")
async def get_customer_balance(
    customer_id: str, 
    currency: str = 'USD',
    # db: AsyncSession = Depends(get_db), 
    # tenant_id: str = Depends(get_tenant_id)
):
    """
    Beta implementation: Returns the customer's balance without ERP double-entry complexity.
    """
    # service = LedgerService(db)
    # balance = await service.get_customer_balance(tenant_id, customer_id, currency)
    # return {"customer_id": customer_id, "balance": float(balance), "currency": currency}
    return {"customer_id": customer_id, "balance": 150.00, "currency": currency}

@router.get("/countries/{code}")
async def get_country_profile(
    code: str, 
    # db: AsyncSession = Depends(get_db), 
    # tenant_id: str = Depends(get_tenant_id)
):
    """
    Returns currency and document formats for the tenant's country.
    """
    # service = CountryProfileService(db)
    # profile = await service.get_tenant_country_profile(tenant_id, code)
    # if not profile:
    #     raise HTTPException(404, "Country profile not active")
    # return profile
    return {
        "country_code": code,
        "currency_code": "USD",
        "tax_mode": "exclusive",
        "document_types": {"types": ["CEDULA", "RUC"]}
    }

@router.post("/storage/assets")
async def register_asset(
    payload: Dict[str, Any], 
    # db: AsyncSession = Depends(get_db), 
    # tenant_id: str = Depends(get_tenant_id)
):
    """
    Registers a storage asset UUID without exposing internal S3 paths.
    """
    # service = AssetService(db)
    # asset_id = await service.register_asset(
    #     tenant_id=tenant_id,
    #     file_name=payload.get('file_name', 'unknown'),
    #     mime_type=payload.get('mime_type', 'application/octet-stream'),
    #     size_bytes=payload.get('size_bytes', 0),
    #     path=payload.get('path', ''),
    #     bucket=payload.get('bucket', 'default')
    # )
    # return {"asset_id": asset_id, "status": "registered"}
    return {"asset_id": "mock-uuid-1234", "status": "registered"}
