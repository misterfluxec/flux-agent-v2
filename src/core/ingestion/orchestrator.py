# =============================================================================
# FLUXAGENT V2 — ORQUESTADOR DE INGESTIÓN
# =============================================================================
# Punto de entrada único para procesar conocimiento y catálogos.
# Coordina FileHandler, CatalogExtractor y VectorIndexer.
# =============================================================================

import logging
from enum import Enum
from uuid import UUID
from typing import Optional, Callable, Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from .file_handler import FileHandler
from .catalog_extractor import CatalogExtractor
from .vector_indexer import VectorIndexer
from core.tasks.progress import report_progress
from core.telemetry.logger import get_logger

logger = get_logger("core.ingestion.orchestrator")

logger = logging.getLogger(__name__)

class IngestMode(Enum):
    RAG_ONLY = "rag"
    CATALOG_ONLY = "catalog"
    BOTH = "both"

class IngestionOrchestrator:
    """
    Fachada profunda que oculta toda la complejidad de la ingesta.
    Se comunica con el exterior mediante callbacks de progreso.
    """
    
    def __init__(
        self, 
        db: AsyncSession,
        file_handler: FileHandler,
        catalog: CatalogExtractor,
        indexer: VectorIndexer
    ):
        self.db = db
        self.files = file_handler
        self.catalog = catalog
        self.indexer = indexer

    async def process_file(
        self, 
        file_path: Optional[str] = None, 
        url: Optional[str] = None,
        tenant_id: UUID = None, 
        mode: IngestMode = IngestMode.BOTH,
        collection_name: str = "default"
    ):
        """
        Orquestación del flujo de ingesta según el modo solicitado.
        """
        try:
            await self._report(10, "Iniciando", "Analizando archivo...")
            
            # --- FLUJO 1: CATÁLOGO (RELACIONAL) ---
            if mode in [IngestMode.CATALOG_ONLY, IngestMode.BOTH]:
                await self._report(30, "Catálogo", "Extrayendo productos estructurados...")
                products = self.catalog.extract(file_path)
                await self._save_products_to_db(products, tenant_id)
                await self._report(60, "Catálogo", f"{len(products)} productos sincronizados.")

            # --- FLUJO 2: RAG (VECTORIAL) ---
            if mode in [IngestMode.RAG_ONLY, IngestMode.BOTH]:
                await self._report(70, "RAG", "Indexando conocimiento para IA...")
                if file_path:
                    await self.indexer.index_file(file_path, tenant_id, collection_name)
                elif url:
                    from services.ingestion import ServicioIngesta
                    ingestor = ServicioIngesta()
                    await ingestor.procesar_url(self.db, url, tenant_id, None)
                
                await self._report(90, "RAG", "Vectores generados correctamente.")

            await self._report(100, "Completado", "Ingesta finalizada con éxito.")
            
        except Exception as e:
            logger.error(f"Error en orquestación de ingesta: {e}")
            await self._report(0, "Error", str(e), status="error")
            raise e
        finally:
            # Cleanup siempre se ejecuta para no llenar el disco de basura
            self.files.cleanup(file_path)

    async def _save_products_to_db(self, products: list, tenant_id: UUID):
        """Persiste los productos en la base de datos SQL."""
        # Nota: Aquí usamos el AsyncSession inyectado respetando RLS
        for p in products:
            await self.db.execute(
                text("""
                    INSERT INTO productos (tenant_id, name, description, price, categoria, metadata)
                    VALUES (:tid, :nom, :desc, :pre, :cat, :meta)
                    ON CONFLICT (tenant_id, name) DO UPDATE 
                    SET description = EXCLUDED.description, price = EXCLUDED.price
                """),
                {
                    "tid": str(tenant_id),
                    "nom": p.get("name"),
                    "desc": p.get("description", ""),
                    "pre": float(p.get("price", 0.0)),
                    "cat": p.get("categoria", "General"),
                    "meta": "{}" # Placeholder para metadatos extra
                }
            )
        await self.db.commit()

    async def _report(self, percentage: int, step: str, message: str, status: str = "processing"):
        """Reporta progreso al emisor global."""
        await report_progress(
            percentage=percentage,
            step=step,
            message=message,
            status=status
        )

import asyncio
