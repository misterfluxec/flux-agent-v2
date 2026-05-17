import hashlib
from typing import Dict, Any
from datetime import datetime, timezone

class CanonicalEntity:
    """
    Entidad normalizada lista para el SyncEngine.
    Representa el contrato oficial interno (ej. Customer, Product).
    """
    def __init__(self, canonical_type: str, external_id: str, payload: Dict[str, Any], updated_at: datetime):
        self.canonical_type = canonical_type
        self.external_id = str(external_id)
        self.payload = payload
        self.updated_at = updated_at
        
    def get_checksum(self) -> str:
        content = f"{self.canonical_type}:{self.external_id}:{self.updated_at.isoformat()}:{str(self.payload)}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()

class SchemaMapper:
    """
    V2 Architecture: SCHEMA TRANSLATOR.
    Traduce la fila cruda obtenida por el conector al model canónico,
    aplicando reglas de normalización y parsing.
    """
    def __init__(self, mapping_json: Dict[str, Any]):
        self.mapping = mapping_json

    def map_to_canonical(self, raw_data: Dict[str, Any], canonical_type: str) -> CanonicalEntity:
        """
        Ej: mapping_json = {"customer_name": "razon_social", "external_id": "dni"}
        """
        entity_mapping = self.mapping.get(canonical_type, {})
        payload = {}
        
        # 1. Extraer ID primario y Timestamp
        external_id_field = entity_mapping.get('_external_id', 'id')
        external_id = raw_data.get(external_id_field)
        
        if not external_id:
            raise ValueError(f"Fila sin identificador externo ({external_id_field})")
            
        updated_at_field = entity_mapping.get('_updated_at', 'updated_at')
        updated_val = raw_data.get(updated_at_field)
        
        # Fallback date logic
        if isinstance(updated_val, datetime):
            updated_at = updated_val
        else:
            updated_at = datetime.now(timezone.utc)
            
        # 2. Mapear Payload
        for canonical_key, raw_key in entity_mapping.items():
            if not canonical_key.startswith('_'): # Ignorar metadata rules (_external_id)
                payload[canonical_key] = raw_data.get(raw_key)
                
        return CanonicalEntity(
            canonical_type=canonical_type,
            external_id=external_id,
            payload=payload,
            updated_at=updated_at
        )
