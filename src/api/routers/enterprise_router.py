from __future__ import annotations
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from auth import get_usuario_actual, PayloadToken
from database import get_db
from services.finance.ledger_service import LedgerService
from services.compliance.country_profile_service import (
    CountryProfileService,
)
from services.storage.asset_service import AssetService

router = APIRouter(
    prefix="/api/v1/enterprise",
    tags=["Enterprise"],
)


# ─── LEDGER ───────────────────────────────────────────────

@router.get("/ledger/balance/{customer_id}")
async def get_customer_balance(
    customer_id: str,
    currency: str = "USD",
    db: AsyncSession = Depends(get_db),
    usuario: PayloadToken = Depends(get_usuario_actual),
):
    """Balance contable del cliente calculado desde el ledger."""
    tenant_id = str(usuario.tenant_id)
    result = await db.execute(
        text("""
            SELECT
                COALESCE(SUM(credit), 0) - COALESCE(SUM(debit), 0)
                AS balance
            FROM flux_ledger_entries
            WHERE tenant_id = :tid
              AND customer_id = :cid
              AND currency   = :cur
        """),
        {"tid": tenant_id, "cid": customer_id, "cur": currency},
    )
    row = result.fetchone()
    balance = float(row.balance) if row and row.balance else 0.0
    return {
        "customer_id": customer_id,
        "tenant_id": tenant_id,
        "balance": balance,
        "currency": currency,
    }


@router.post("/ledger/payment")
async def record_payment(
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    usuario: PayloadToken = Depends(get_usuario_actual),
):
    """Registra un pago recibido en el ledger de doble entrada."""
    tenant_id = str(usuario.tenant_id)
    service = LedgerService(db)
    await service.record_payment_received(
        tenant_id=tenant_id,
        customer_id=payload["customer_id"],
        amount=Decimal(str(payload["amount"])),
        currency=payload.get("currency", "USD"),
        reference_id=payload["reference_id"],
    )
    return {"status": "recorded", "tenant_id": tenant_id}


@router.post("/ledger/refund")
async def record_refund(
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    usuario: PayloadToken = Depends(get_usuario_actual),
):
    """Registra un reembolso emitido."""
    tenant_id = str(usuario.tenant_id)
    service = LedgerService(db)
    await service.record_refund_issued(
        tenant_id=tenant_id,
        customer_id=payload["customer_id"],
        amount=Decimal(str(payload["amount"])),
        currency=payload.get("currency", "USD"),
        reference_id=payload["reference_id"],
    )
    return {"status": "recorded", "tenant_id": tenant_id}


# ─── COUNTRY PROFILES ─────────────────────────────────────

@router.get("/countries/{code}")
async def get_country_profile(
    code: str,
    db: AsyncSession = Depends(get_db),
    usuario: PayloadToken = Depends(get_usuario_actual),
):
    """Configuración operativa del tenant para un país LATAM."""
    tenant_id = str(usuario.tenant_id)
    service = CountryProfileService(db)
    profile = await service.get_tenant_country_profile(
        tenant_id, code.upper()
    )
    if not profile:
        raise HTTPException(
            status_code=404,
            detail=f"País '{code}' no configurado para este tenant.",
        )
    return profile


@router.post("/countries/{code}/validate-document")
async def validate_document(
    code: str,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    usuario: PayloadToken = Depends(get_usuario_actual),
):
    """Valida si un type de documento es válido para el país."""
    tenant_id = str(usuario.tenant_id)
    service = CountryProfileService(db)
    valid = await service.validate_document_type(
        tenant_id=tenant_id,
        country_code=code.upper(),
        doc_type=payload.get("doc_type", ""),
    )
    return {"valid": valid, "doc_type": payload.get("doc_type")}


# ─── ASSETS ───────────────────────────────────────────────

@router.post("/storage/assets")
async def register_asset(
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    usuario: PayloadToken = Depends(get_usuario_actual),
):
    """Registra metadata de un asset ya subido al storage."""
    tenant_id = str(usuario.tenant_id)
    service = AssetService(db)
    asset_id = await service.register_asset(
        tenant_id=tenant_id,
        file_name=payload["file_name"],
        mime_type=payload.get("mime_type", "application/octet-stream"),
        size_bytes=int(payload.get("size_bytes", 0)),
        path=payload["path"],
        bucket=payload.get("bucket", "default"),
    )
    return {"asset_id": asset_id, "tenant_id": tenant_id}


@router.get("/storage/assets/{asset_id}")
async def get_asset(
    asset_id: str,
    db: AsyncSession = Depends(get_db),
    usuario: PayloadToken = Depends(get_usuario_actual),
):
    """Recupera metadata de un asset por ID."""
    tenant_id = str(usuario.tenant_id)
    service = AssetService(db)
    asset = await service.get_asset_metadata(
        tenant_id=tenant_id,
        asset_id=asset_id,
    )
    if not asset:
        raise HTTPException(
            status_code=404, detail="Asset no encontrado."
        )
    return asset
