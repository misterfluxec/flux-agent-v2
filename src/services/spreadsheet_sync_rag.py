import httpx
import logging
import csv
import io
from datetime import datetime
from typing import List, Dict, Tuple
from sqlalchemy import text

from config import obtener_config
config = obtener_config()
from database import obtener_sesion

logger = logging.getLogger(__name__)

class RAGSyncEngine:
    """
    Motor de sincronización: Sheets/Excel -> Ollama (Embeddings) -> PostgreSQL (pgvector)
    """
    
    COLUMN_HEURISTICS = {
        "nombre": ["nombre", "producto", "item", "artículo", "title", "name", "articulo"],
        "precio": ["precio", "costo", "valor", "price", "cost", "amount"],
        "stock": ["stock", "cantidad", "disponible", "inventario", "quantity", "available"],
        "sku": ["sku", "código", "codigo", "id", "reference"],
        "descripcion": ["descripción", "descripcion", "desc", "details", "description"],
        "categoria": ["categoría", "categoria", "category", "tipo", "type"],
    }
    
    @classmethod
    def detect_column_mapping(cls, headers: List[str]) -> Dict[str, str]:
        mapping = {}
        for internal_field, keywords in cls.COLUMN_HEURISTICS.items():
            for header in headers:
                if header in keywords:
                    mapping[internal_field] = header
                    break
                elif any(kw in header for kw in keywords):
                    mapping[internal_field] = header
                    break
        return mapping
        
    @classmethod
    async def fetch_google_sheet_data(cls, access_token: str, sheet_id: str, range_name: str = "Hoja1!A1:Z1000") -> Tuple[List[str], List[Dict]]:
        url = f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/{range_name}"
        headers = {"Authorization": f"Bearer {access_token}"}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            
        values = data.get("values", [])
        if not values:
            return [], []
            
        headers = [str(h).strip().lower() for h in values[0]]
        rows = []
        for row in values[1:]:
            row_dict = {headers[i]: row[i].strip() if i < len(row) else "" for i in range(len(headers))}
            if any(v for v in row_dict.values()):
                rows.append(row_dict)
                
        return headers, rows

    @classmethod
    async def fetch_excel_online_data(cls, access_token: str, file_id: str) -> Tuple[List[str], List[Dict]]:
        graph_url = f"https://graph.microsoft.com/v1.0/me/drive/items/{file_id}"
        headers = {"Authorization": f"Bearer {access_token}"}
        
        async with httpx.AsyncClient() as client:
            meta_resp = await client.get(graph_url, headers=headers)
            meta_resp.raise_for_status()
            
            download_url = f"{graph_url}/content"
            csv_resp = await client.get(download_url, headers=headers)
            csv_resp.raise_for_status()
            
            reader = csv.DictReader(io.StringIO(csv_resp.text))
            rows = list(reader)
            
            if not rows:
                return [], []
            
            headers = [h.strip().lower() for h in rows[0].keys()]
            return headers, rows

    @classmethod
    async def process_sheet_for_rag(cls, tenant_id: str, agent_id: str, synced_source_id: str, rows: List[Dict], column_mapping: Dict) -> Dict:
        """
        Procesa filas y las vectoriza a knowledge_chunks.
        Retorna estadísticas.
        """
        stats = {"added": 0, "errors": 0}
        chunks_to_insert = []
        
        for row in rows:
            try:
                semantic_text = cls._build_semantic_context(row, column_mapping)
                embedding = await cls._generate_embedding(semantic_text)
                
                chunks_to_insert.append({
                    "tenant_id": str(tenant_id),
                    "agent_id": str(agent_id),
                    "synced_source_id": str(synced_source_id),
                    "fuente_tipo": "excel",
                    "contenido": semantic_text,
                    "embedding": embedding
                })
            except Exception as e:
                logger.error(f"Error vectorizando fila: {e}")
                stats["errors"] += 1

        if not chunks_to_insert:
            return stats

        async with obtener_sesion() as db:
            async with db.begin():
                # 1. Limpiar chunks antiguos del sync anterior
                await db.execute(text("""
                    DELETE FROM knowledge_chunks 
                    WHERE agent_id = :agent_id AND synced_source_id = :synced_source_id
                """), {"agent_id": str(agent_id), "synced_source_id": str(synced_source_id)})
                
                # 2. Insertar en lotes
                batch_size = 50
                for i in range(0, len(chunks_to_insert), batch_size):
                    batch = chunks_to_insert[i:i+batch_size]
                    await db.execute(text("""
                        INSERT INTO knowledge_chunks 
                        (tenant_id, agent_id, synced_source_id, fuente_tipo, contenido, embedding, creado_en)
                        VALUES (:tenant_id, :agent_id, :synced_source_id, :fuente_tipo, :contenido, :embedding::vector, NOW())
                    """), batch)
                    stats["added"] += len(batch)

        return stats

    @staticmethod
    def _build_semantic_context(row: Dict, mapping: Dict) -> str:
        nombre = row.get(mapping.get('nombre', ''), 'Producto Desconocido')
        precio = row.get(mapping.get('precio', ''), 'N/A')
        sku = row.get(mapping.get('sku', ''), 'N/A')
        stock = row.get(mapping.get('stock', ''), 'N/A')
        desc = row.get(mapping.get('descripcion', ''), '')
        cat = row.get(mapping.get('categoria', ''), '')
        return f"[Producto] {nombre}. [SKU] {sku}. [Precio] {precio}. [Stock] {stock}. [Categoría] {cat}. [Descripción] {desc}"

    @classmethod
    async def _generate_embedding(cls, text_content: str) -> List[float]:
        ollama_url = getattr(config, 'ollama_base_url', 'http://ollama:11434')
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{ollama_url}/api/embeddings",
                json={"model": "nomic-embed-text", "prompt": text_content},
                timeout=30.0
            )
            response.raise_for_status()
            return response.json().get("embedding")
