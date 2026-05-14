from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional, Dict, Any
import logging
from uuid import UUID

logger = logging.getLogger(__name__)

class AssetService:
    """
    Sprint H3: Storage & Custody Abstraction.
    Resolves UUIDs back to physical URLs/paths and handles storage metadata.
    Prevents leaking raw S3 buckets or local paths directly into frontend payloads.
    """
    def __init__(self, db: AsyncSession, storage_provider: Any = None):
        self.db = db
        self.provider = storage_provider # S3, GCS, or Local

    async def register_asset(self, tenant_id: str, file_name: str, mime_type: str, size_bytes: int, path: str, bucket: str = "default") -> str:
        """
        Registers a new uploaded asset in the database and returns its UUID.
        """
        stmt = text("""
            INSERT INTO storage_assets 
            (tenant_id, storage_provider, bucket, path, file_name, mime_type, size_bytes)
            VALUES 
            (:tenant_id, :provider, :bucket, :path, :file_name, :mime_type, :size_bytes)
            RETURNING id
        """)
        
        provider_name = "local" if not self.provider else self.provider.name
        
        result = await self.db.execute(stmt, {
            "tenant_id": tenant_id,
            "provider": provider_name,
            "bucket": bucket,
            "path": path,
            "file_name": file_name,
            "mime_type": mime_type,
            "size_bytes": size_bytes
        })
        
        asset_id = result.scalar()
        logger.info(f"[Storage] Registered asset {asset_id} for tenant {tenant_id}")
        return str(asset_id)

    async def get_asset_metadata(self, tenant_id: str, asset_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the metadata for an asset to serve it or process it.
        """
        stmt = text("""
            SELECT id, file_name, mime_type, size_bytes, virus_scan_status, storage_provider, bucket, path
            FROM storage_assets
            WHERE id = :asset_id AND tenant_id = :tenant_id
        """)
        
        result = await self.db.execute(stmt, {
            "asset_id": asset_id,
            "tenant_id": tenant_id
        })
        
        row = result.fetchone()
        if not row:
            return None
            
        # row._mapping is useful but we return a clean dict
        return {
            "id": str(row[0]),
            "file_name": row[1],
            "mime_type": row[2],
            "size_bytes": row[3],
            "virus_scan_status": row[4],
            "provider": row[5],
            "bucket": row[6],
            "path": row[7]
        }
