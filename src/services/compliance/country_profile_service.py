from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class CountryProfileService:
    """
    Sprint H3: Multi-Country LATAM Abstraction (Beta Level).
    Provides configuration for currency, tax modes, and valid document formats.
    Complex fiscal logic (like SAT/SRI XML signatures) is deferred to v1.1.
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_tenant_country_profile(self, tenant_id: str, country_code: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the operational configuration for a tenant in a specific country.
        """
        stmt = text("""
            SELECT currency_code, tax_mode, invoice_strategy, phone_prefix, timezone, document_types
            FROM country_profiles
            WHERE tenant_id = :tenant_id AND country_code = :country_code AND is_active = TRUE
        """)
        
        result = await self.db.execute(stmt, {
            "tenant_id": tenant_id,
            "country_code": country_code
        })
        
        row = result.fetchone()
        if not row:
            return None
            
        return {
            "country_code": country_code,
            "currency_code": row[0],
            "tax_mode": row[1],
            "invoice_strategy": row[2],
            "phone_prefix": row[3],
            "timezone": row[4],
            "document_types": row[5] # JSON containing list of valid IDs (RUC, NIT, etc)
        }

    async def validate_document_type(self, tenant_id: str, country_code: str, doc_type: str) -> bool:
        """
        Checks if a given document type (e.g. 'RUC', 'CEDULA') is valid for the tenant's country profile.
        """
        profile = await self.get_tenant_country_profile(tenant_id, country_code)
        if not profile or not profile.get("document_types"):
            return False
            
        valid_types = profile["document_types"].get("types", [])
        return doc_type.upper() in [t.upper() for t in valid_types]
