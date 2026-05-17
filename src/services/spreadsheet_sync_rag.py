import httpx
import logging
import csv
import io
from datetime import datetime
from typing import List, Dict, Tuple
from sqlalchemy import text

from config import obtener_config
config = obtener_config()
from database import SesionLocal

logger = logging.getLogger(__name__)

class RAGSyncEngine:
    """
    Motor de sincronización: Sheets/Excel -> Ollama (Embeddings) -> PostgreSQL (pgvector)
    """
    
    COLUMN_HEURISTICS = {
        "name": ["name", "producto", "item", "artículo", "title", "name", "articulo"],
        "price": ["price", "costo", "valor", "price", "cost", "amount"],
        "stock": ["stock", "cantidad", "disponible", "inventario", "quantity", "available"],
        "sku": ["sku", "código", "codigo", "id", "reference"],
        "description": ["descripción", "description", "desc", "details", "description"],
        "categoria": ["categoría", "categoria", "category", "type", "type"],
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
    async def fetch_local_file_data(cls, file_name: str) -> Tuple[List[str], List[Dict]]:
        import os
        import pandas as pd
        local_path = os.path.join("uploads/temp", file_name)
        if not os.path.exists(local_path):
            raise FileNotFoundError(f"El archivo local {file_name} no se encontró.")
            
        ext = local_path.split(".")[-1].lower() if "." in local_path else ""
        if ext == "csv":
            try:
                df = pd.read_csv(local_path, sep=",")
            except:
                df = pd.read_csv(local_path, sep=";")
        elif ext in ["xlsx", "xls"]:
            df = pd.read_excel(local_path)
        else:
            raise ValueError(f"Formato de archivo local no soportado para sync: {ext}")
            
        df = df.dropna(how="all")
        headers = [str(col).strip().lower() for col in df.columns]
        rows = df.replace({pd.NA: None, float('nan'): None}).to_dict(orient="records")
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
                    "agent_id": str(agent_id) if agent_id else None,
                    "synced_source_id": str(synced_source_id),
                    "fuente_tipo": "excel",
                    "contenido": semantic_text,
                    "embedding": str(embedding)
                })
            except Exception as e:
                logger.error(f"Error vectorizando fila: {e}")
                stats["errors"] += 1

        if not chunks_to_insert:
            return stats

        async with SesionLocal() as db:
            async with db.begin():
                # 1. Limpiar chunks antiguos del sync anterior
                await db.execute(text("""
                    DELETE FROM knowledge_chunks 
                    WHERE agent_id = :agent_id AND fuente_nombre = :synced_source_id
                """), {"agent_id": str(agent_id) if agent_id else None, "synced_source_id": str(synced_source_id)})
                
                # 2. Insertar en lotes a knowledge_chunks y catalog_items
                batch_size = 50
                for i in range(0, len(chunks_to_insert), batch_size):
                    batch = chunks_to_insert[i:i+batch_size]
                    
                    # RAG Insert
                    await db.execute(text("""
                        INSERT INTO knowledge_chunks 
                        (tenant_id, agent_id, fuente_nombre, fuente_tipo, contenido, embedding, created_at)
                        VALUES (:tenant_id, :agent_id, :synced_source_id, :fuente_tipo, :contenido, CAST(:embedding AS vector), NOW())
                    """), batch)
                    stats["added"] += len(batch)
                    
                # 3. Upsert to catalog_items
                catalog_batch = []
                for row in rows:
                    try:
                        name = row.get(column_mapping.get('name', ''), '')
                        if not name:
                            continue
                            
                        # Try to cast price and stock safely
                        try:
                            price_str = str(row.get(column_mapping.get('price', ''), '0')).replace(',', '').replace('$', '')
                            price = float(price_str) if price_str.strip() else 0.0
                        except:
                            price = 0.0
                            
                        try:
                            stock_str = str(row.get(column_mapping.get('stock', ''), '0'))
                            stock = int(float(stock_str)) if stock_str.strip() else 0
                        except:
                            stock = 0
                            
                        desc = row.get(column_mapping.get('description', ''), '')
                        cat = row.get(column_mapping.get('categoria', ''), '')
                        
                        catalog_batch.append({
                            "tenant_id": str(tenant_id),
                            "type": "physical_product",
                            "name": name[:255],
                            "description": desc,
                            "base_price": price,
                            "stock_quantity": stock,
                            "metadata": '{"category": "' + cat.replace('"', '\\"') + '"}'
                        })
                    except Exception as e:
                        logger.error(f"Error mapping catalog item: {e}")
                
                if catalog_batch:
                    # Execute in smaller batches if many items
                    for i in range(0, len(catalog_batch), 50):
                        cb = catalog_batch[i:i+50]
                        await db.execute(text("""
                            INSERT INTO catalog_items 
                            (tenant_id, type, name, description, base_price, stock_quantity, metadata, updated_at)
                            VALUES (:tenant_id, :type, :name, :description, :base_price, :stock_quantity, CAST(:metadata AS jsonb), NOW())
                            ON CONFLICT (tenant_id, name) DO UPDATE SET
                                description = EXCLUDED.description,
                                base_price = EXCLUDED.base_price,
                                stock_quantity = EXCLUDED.stock_quantity,
                                metadata = EXCLUDED.metadata,
                                updated_at = NOW()
                        """), cb)

        return stats

    @staticmethod
    def _build_semantic_context(row: Dict, mapping: Dict) -> str:
        name = row.get(mapping.get('name', ''), 'Producto Desconocido')
        price = row.get(mapping.get('price', ''), 'N/A')
        sku = row.get(mapping.get('sku', ''), 'N/A')
        stock = row.get(mapping.get('stock', ''), 'N/A')
        desc = row.get(mapping.get('description', ''), '')
        cat = row.get(mapping.get('categoria', ''), '')
        return f"[Producto] {name}. [SKU] {sku}. [Precio] {price}. [Stock] {stock}. [Categoría] {cat}. [Descripción] {desc}"

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
