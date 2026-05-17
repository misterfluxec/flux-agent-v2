# =============================================================================
# FLUXAGENT V2 — INDEXADOR VECTORIAL (RAG)
# =============================================================================
# Gestión de chunking, embeddings y persistencia en pgvector.
# =============================================================================

import logging
import asyncio
from typing import List, Dict, Any, Optional
from uuid import UUID

logger = logging.getLogger(__name__)

class VectorIndexer:
    """
    Gestiona la transformación de texto en vectores y su almacenamiento.
    Aísla la lógica RAG de la lógica relacional.
    """
    
    def __init__(self, embedding_model: str = "nomic-embed-text"):
        self.model = embedding_model

    async def index_text(self, text: str, tenant_id: UUID, collection_name: str, metadata: Dict[str, Any] = {}):
        """
        Divide el texto en chunks, genera embeddings y los guarda.
        """
        # 1. Chunking (Locality: La lógica de segmentación vive aquí)
        chunks = self._chunk_text(text, size=1000, overlap=100)
        
        # 2. Embeddings y Persistencia
        # En una versión profunda, esto llamaría a un VectorStoreWrapper
        from services.ingestion import ServicioIngesta # Fallback temporal mientras refactorizamos ServicioIngesta
        ingestor = ServicioIngesta() 
        
        # Procesamos cada chunk
        for i, chunk in enumerate(chunks):
            chunk_metadata = {**metadata, "chunk_index": i}
            # Llamamos a la lógica vectorial existente (que ya maneja pgvector)
            await ingestor.crear_embedding_y_guardar(
                texto=chunk,
                tenant_id=tenant_id,
                coleccion=collection_name,
                metadata=chunk_metadata
            )
        
        logger.info(f"Indexados {len(chunks)} chunks en colección '{collection_name}' (Tenant: {tenant_id})")

    def _chunk_text(self, text: str, size: int, overlap: int) -> List[str]:
        """Divide texto en fragmentos con solapamiento."""
        if not text: return []
        chunks = []
        for i in range(0, len(text), size - overlap):
            chunks.append(text[i:i + size])
        return chunks

    async def index_file(self, file_path: str, tenant_id: UUID, collection_name: str):
        """Lee un archivo según su type y lo indexa para RAG."""
        from services.ingestion import ServicioIngesta
        ingestor = ServicioIngesta()
        
        # Usamos los extractores de texto existentes por ahora para no duplicar código
        # pero los llamamos desde aquí para mantener el control del orquestador.
        ext = os.path.splitext(file_path)[1].lower()
        texto = ""
        
        if ext == ".pdf":
            texto = ingestor.extraer_texto_pdf(file_path)
        elif ext == ".txt":
            with open(file_path, 'r', encoding='utf-8') as f:
                texto = f.read()
        # ... otros formatos ...
        
        if texto:
            await self.index_text(texto, tenant_id, collection_name, {"source": os.path.basename(file_path)})

import os
