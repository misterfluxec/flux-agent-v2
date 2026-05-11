from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime

class BaseDataConnector(ABC):
    """
    V2 Architecture: PURE DATA EXTRACTOR.
    El conector solo sabe extraer diccionarios crudos de la fuente.
    NO sabe de 'Customers', 'Products', o Mappings. Solo extrae 'entidades'.
    """
    def __init__(self, config_encrypted: Dict[str, Any]):
        self.config = config_encrypted

    @abstractmethod
    async def connect(self) -> bool:
        """Establece conexión y valida credenciales."""
        pass

    @abstractmethod
    async def fetch_raw_data(self, entity_name: str, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Extrae datos crudos de una entidad específica (ej. 'clientes', 'Hoja 1').
        """
        pass
