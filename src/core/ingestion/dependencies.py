# =============================================================================
# FLUXAGENT V2 — DEPENDENCIAS DE INGESTIÓN
# =============================================================================

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database import obtener_sesion
from core.task_runner import task_runner
from .file_handler import FileHandler
from .catalog_extractor import CatalogExtractor
from .vector_indexer import VectorIndexer
from .orchestrator import IngestionOrchestrator

def get_file_handler() -> FileHandler:
    return FileHandler()

def get_catalog_extractor() -> CatalogExtractor:
    return CatalogExtractor()

def get_vector_indexer() -> VectorIndexer:
    return VectorIndexer()

async def get_ingestion_orchestrator(
    db: AsyncSession = Depends(obtener_sesion),
    file_h: FileHandler = Depends(get_file_handler),
    catalog: CatalogExtractor = Depends(get_catalog_extractor),
    indexer: VectorIndexer = Depends(get_vector_indexer)
) -> IngestionOrchestrator:
    """
    Proporciona un orquestador configurado. 
    Nota: El callback de progreso se inyectará en el momento de la llamada
    para vincularlo al task_id dinámico.
    """
    return IngestionOrchestrator(
        db=db,
        file_handler=file_h,
        catalog=catalog,
        indexer=indexer
    )

def create_progress_callback(task_id: str, tenant_id: str):
    """
    Bridge entre el Orquestador y el TaskRunner/WebSockets.
    Esto evita que el Orquestador sepa de Redis.
    """
    async def callback(percentage: int, step: str, message: str, status: str):
        task_runner.update_progress(
            task_id=task_id,
            percentage=percentage,
            step=step,
            message=message,
            status=status,
            tenant_id=tenant_id
        )
    return callback
