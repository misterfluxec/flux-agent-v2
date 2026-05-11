import hashlib
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

class ConnectorEntity(ABC):
    """
    Entidad base para sincronización. 
    Contiene la data cruda del ERP y su lógica de Checksum (Idempotencia).
    """
    def __init__(self, data: Dict[str, Any]):
        self.data = data
        self.external_id = str(data.get('external_id') or data.get('id') or '')
        
        # Intentar extraer timestamp de actualización del ERP, si no usar now
        updated_val = data.get('updated_at') or data.get('modified_at') or data.get('modified_date')
        if isinstance(updated_val, datetime):
            self.updated_at = updated_val
        elif isinstance(updated_val, str):
            try:
                # Simplificación: intentar parsear ISO
                self.updated_at = datetime.fromisoformat(updated_val.replace('Z', '+00:00'))
            except Exception:
                self.updated_at = datetime.now(timezone.utc)
        else:
            self.updated_at = datetime.now(timezone.utc)
    
    def get_checksum(self) -> str:
        """Genera hash MD5 para detección de cambios (Deltas)."""
        # Se asume que external_id y la data en string representan el estado exacto
        content = f"{self.external_id}:{self.updated_at.isoformat()}:{str(self.data)}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()

class ERPConnectorInterface(ABC):
    """
    Interfaz base oficial para todos los conectores ERP / Fuentes de Datos.
    """
    
    # Declaración de capacidades soportadas por defecto (a sobrescribir por hijos)
    capabilities = {
        "customers": False,
        "products": False,
        "inventory": False,
        "orders": False,
    }
    
    def __init__(self, tenant_id: str, config: Dict[str, Any]):
        self.tenant_id = tenant_id
        self.config = config
        self.last_sync = None
    
    @abstractmethod
    async def connect(self) -> bool:
        """Establece conexión con el sistema externo o valida acceso al archivo."""
        pass
    
    @abstractmethod
    async def fetch_customers(self, since: Optional[datetime] = None) -> List[ConnectorEntity]:
        """Obtiene lista de clientes desde la fuente, opcionalmente los modificados después de 'since'."""
        pass
    
    @abstractmethod
    async def fetch_products(self, since: Optional[datetime] = None) -> List[ConnectorEntity]:
        """Obtiene productos y/o inventario base."""
        pass
    
    @abstractmethod
    async def fetch_inventory(self, since: Optional[datetime] = None) -> List[ConnectorEntity]:
        """Obtiene niveles de stock de inventario (separado de producto si aplica)."""
        pass
        
    @abstractmethod
    async def fetch_orders(self, since: Optional[datetime] = None) -> List[ConnectorEntity]:
        """Obtiene órdenes históricas."""
        pass
    
    @abstractmethod
    async def push_order(self, order_data: Dict[str, Any]) -> str:
        """Escribe/Envía una orden al ERP."""
        pass
    
    async def test_connection(self) -> Dict[str, Any]:
        """Prueba estandarizada de conectividad y capacidades."""
        try:
            connected = await self.connect()
            return {
                "status": "connected" if connected else "failed",
                "connector": self.__class__.__name__,
                "capabilities": self.capabilities,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "connector": self.__class__.__name__,
                "capabilities": self.capabilities
            }
