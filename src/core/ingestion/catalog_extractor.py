# =============================================================================
# FLUXAGENT V2 — EXTRACTOR DE CATÁLOGO (SQL)
# =============================================================================
# Transforma archivos estructurados en modelos de productos relacionales.
# =============================================================================

import pandas as pd
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger(__name__)

class ProductSchema(BaseModel):
    """Modelo de datos para un producto en el catálogo."""
    name: str
    description: Optional[str] = ""
    price: float = 0.0
    categoria: Optional[str] = "General"
    stock: Optional[int] = 0
    sku: Optional[str] = None
    metadata: Dict[str, Any] = {}

class CatalogExtractor:
    """
    Se encarga de la extracción pura de datos estructurados.
    Independiente de la lógica de vectores o de la base de datos.
    """
    
    def extract(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Lee Excel o CSV y retorna una lista de diccionarios normalizados.
        """
        ext = os.path.splitext(file_path)[1].lower()
        
        try:
            if ext == ".xlsx":
                df = pd.read_excel(file_path)
            elif ext == ".csv":
                df = pd.read_csv(file_path)
            else:
                raise ValueError(f"Formato no soportado para catálogo: {ext}")
            
            # Normalización de columnas (Case insensitive match)
            df.columns = [c.lower().strip() for c in df.columns]
            
            # Mapeo inteligente (MVP)
            # Buscamos columnas que se parezcan a nuestros campos
            column_map = {
                "name": "name", "producto": "name", "item": "name",
                "price": "price", "costo": "price", "valor": "price",
                "description": "description", "detalle": "description",
                "category": "categoria", "type": "categoria"
            }
            
            # Renombrar si existen coincidencias
            for col in df.columns:
                if col in column_map:
                    df.rename(columns={col: column_map[col]}, inplace=True)
            
            # Convertir a lista de dicts y validar mínimamente
            products = df.to_dict(orient="records")
            logger.info(f"Extraídos {len(products)} posibles productos de {file_path}")
            
            return products
            
        except Exception as e:
            logger.error(f"Error en extracción de catálogo: {e}")
            raise RuntimeError(f"Fallo al procesar el archivo de catálogo: {str(e)}")

# Necesitamos import os para las extensiones
import os
from typing import Optional
