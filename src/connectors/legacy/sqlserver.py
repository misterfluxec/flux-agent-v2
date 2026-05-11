from typing import List, Dict, Any, Optional
from datetime import datetime

from connectors.legacy.base import ERPConnectorInterface, ConnectorEntity

class SQLServerEntity(ConnectorEntity):
    """Mapeo Dinámico de SQL Server → Canonical Model"""
    def __init__(self, data: Dict[str, Any], mapping: Dict[str, str]):
        mapped_data = {}
        for canonical_key, sql_column in mapping.items():
            mapped_data[canonical_key] = data.get(sql_column)
            
        super().__init__(mapped_data)
        
        # Atributos explícitos expuestos para facilitar el SyncEngine
        self.first_name = mapped_data.get('first_name')
        self.last_name = mapped_data.get('last_name')
        self.email = mapped_data.get('email')
        self.phone = mapped_data.get('phone')
        self.tax_id = mapped_data.get('tax_id')
        
        self.sku = mapped_data.get('sku')
        self.name = mapped_data.get('name')
        self.stock = mapped_data.get('stock')
        self.price = mapped_data.get('price')

class SQLServerConnector(ERPConnectorInterface):
    """
    Conector para SQL Server (ERPs Windows/legacy LATAM).
    Soporta mapeo dinámico de tablas y columnas (Tier 1 Priority).
    """
    
    capabilities = {
        "customers": True,
        "products": True,
        "inventory": True,
        "orders": False, # Future phase
    }
    
    def __init__(self, tenant_id: str, config: Dict[str, Any]):
        super().__init__(tenant_id, config)
        self.connection = None
        
        # DB Config
        self.server = config.get('server')
        self.database = config.get('database')
        self.username = config.get('username')
        self.password = config.get('password')
        
        # Dynamic Mapping
        self.tables = config.get('tables', {
            'customers': 'Clientes',
            'products': 'Articulos'
        })
        self.customers_mapping = config.get('customers_mapping', {})
        self.products_mapping = config.get('products_mapping', {})
        
        # Fecha de modificación en el ERP (ej. 'FechaModificacion', 'updated_at')
        self.updated_at_column = config.get('updated_at_column', 'updated_at')
    
    async def connect(self) -> bool:
        """Conecta a SQL Server usando pyodbc."""
        try:
            import pyodbc
        except ImportError:
            print("❌ pyodbc no está instalado. No se puede conectar a SQL Server.")
            return False
        try:
            conn_str = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={self.server};"
                f"DATABASE={self.database};"
                f"UID={self.username};"
                f"PWD={self.password}"
            )
            self.connection = pyodbc.connect(conn_str, timeout=10)
            return True
        except Exception as e:
            print(f"❌ SQL Server connection failed: {e}")
            return False
            
    def _execute_query(self, query: str, params: List[Any]) -> List[Dict[str, Any]]:
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        columns = [column[0] for column in cursor.description]
        
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        return results
    
    async def fetch_customers(self, since: Optional[datetime] = None) -> List[SQLServerEntity]:
        if not self.customers_mapping:
            return []
            
        if not self.connection:
            await self.connect()
        
        table = self.tables.get('customers', 'Customers')
        query = f"SELECT * FROM {table}"
        params = []
        
        if since:
            query += f" WHERE {self.updated_at_column} > ?"
            params.append(since)
            
        raw_data = self._execute_query(query, params)
        
        entities = []
        for row in raw_data:
            entity = SQLServerEntity(row, self.customers_mapping)
            if entity.external_id:
                entities.append(entity)
        return entities
    
    async def fetch_products(self, since: Optional[datetime] = None) -> List[SQLServerEntity]:
        if not self.products_mapping:
            return []
            
        if not self.connection:
            await self.connect()
        
        table = self.tables.get('products', 'Products')
        query = f"SELECT * FROM {table}"
        params = []
        
        if since:
            query += f" WHERE {self.updated_at_column} > ?"
            params.append(since)
            
        raw_data = self._execute_query(query, params)
        
        entities = []
        for row in raw_data:
            entity = SQLServerEntity(row, self.products_mapping)
            if entity.external_id:
                entities.append(entity)
        return entities

    async def fetch_inventory(self, since: Optional[datetime] = None) -> List[ConnectorEntity]:
        return await self.fetch_products(since)

    async def fetch_orders(self, since: Optional[datetime] = None) -> List[ConnectorEntity]:
        return []

    async def push_order(self, order_data: Dict[str, Any]) -> str:
        raise NotImplementedError("Push de órdenes requiere configuración específica del ERP")
    
    def __del__(self):
        if self.connection:
            self.connection.close()
