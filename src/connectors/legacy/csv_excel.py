import io
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime
from connectors.legacy.base import ERPConnectorInterface, ConnectorEntity

class GenericSheetEntity(ConnectorEntity):
    """Entidad genérica extraída de Hojas de Cálculo (CSV, Excel, Google Sheets)"""
    def __init__(self, data: Dict[str, Any], mapping: Dict[str, str]):
        # data = raw row from pandas
        # mapping = {"sku": "Código", "price": "Precio Venta"}
        
        mapped_data = {}
        for canonical_key, sheet_column in mapping.items():
            mapped_data[canonical_key] = data.get(sheet_column)
            
        # Pasar a la base: el external_id debe estar mapeado
        super().__init__(mapped_data)
        
        # Atributos expuestos directamente si fueron mapeados
        self.first_name = mapped_data.get('first_name')
        self.last_name = mapped_data.get('last_name')
        self.email = mapped_data.get('email')
        self.phone = mapped_data.get('phone')
        self.tax_id = mapped_data.get('tax_id')
        
        self.sku = mapped_data.get('sku')
        self.name = mapped_data.get('name')
        self.stock = mapped_data.get('stock')
        self.price = mapped_data.get('price')

class CSVExcelConnector(ERPConnectorInterface):
    """
    Conector Universal para Archivos (CSV, XLSX) y Google Sheets.
    El 90% de las PYMES LATAM adoptarán la plataforma por este conector.
    """
    
    capabilities = {
        "customers": True,
        "products": True,
        "inventory": True,
        "orders": False,  # Leer órdenes históricas de Excel es raro, pero posible si se configura.
    }
    
    def __init__(self, tenant_id: str, config: Dict[str, Any]):
        super().__init__(tenant_id, config)
        # config ej:
        # {
        #   "source_type": "url" | "file",
        #   "url": "https://docs.google.com/spreadsheets/d/.../export?format=csv",
        #   "file_path": "/var/uploads/tenant_123.xlsx",
        #   "customers_mapping": {"external_id": "DNI", "first_name": "Nombre", "email": "Correo"},
        #   "products_mapping": {"external_id": "SKU", "name": "Descripción", "price": "PVP", "stock": "Inventario"}
        # }
        self.source_type = config.get('source_type', 'file')
        self.url = config.get('url')
        self.file_path = config.get('file_path')
        self.customers_mapping = config.get('customers_mapping', {})
        self.products_mapping = config.get('products_mapping', {})
    
    def _read_dataframe(self) -> pd.DataFrame:
        """Helper para leer pandas DF según la fuente."""
        try:
            if self.source_type == 'url' and self.url:
                # Soporta URLs de Google Sheets (export?format=csv)
                if 'csv' in self.url.lower():
                    return pd.read_csv(self.url)
                else:
                    return pd.read_excel(self.url)
            elif self.source_type == 'file' and self.file_path:
                if self.file_path.endswith('.csv'):
                    return pd.read_csv(self.file_path)
                else:
                    return pd.read_excel(self.file_path)
            raise ValueError("No se configuró una fuente válida (url o file_path).")
        except Exception as e:
            raise Exception(f"Fallo al leer la hoja de cálculo: {e}")

    async def connect(self) -> bool:
        """Valida lectura del primer kilobyte / primera fila."""
        try:
            df = self._read_dataframe()
            return not df.empty
        except Exception:
            return False

    async def fetch_customers(self, since: Optional[datetime] = None) -> List[GenericSheetEntity]:
        if not self.customers_mapping:
            return []
            
        df = self._read_dataframe()
        customers = []
        for _, row in df.iterrows():
            data_dict = row.to_dict()
            entity = GenericSheetEntity(data_dict, self.customers_mapping)
            if entity.external_id:  # Debe tener ID para sincronizarse
                customers.append(entity)
        return customers

    async def fetch_products(self, since: Optional[datetime] = None) -> List[GenericSheetEntity]:
        if not self.products_mapping:
            return []
            
        df = self._read_dataframe()
        products = []
        for _, row in df.iterrows():
            data_dict = row.to_dict()
            entity = GenericSheetEntity(data_dict, self.products_mapping)
            if entity.external_id:
                products.append(entity)
        return products

    async def fetch_inventory(self, since: Optional[datetime] = None) -> List[GenericSheetEntity]:
        # El inventario a menudo viene con el maestro de productos en Excel.
        return await self.fetch_products(since)

    async def fetch_orders(self, since: Optional[datetime] = None) -> List[ConnectorEntity]:
        return []

    async def push_order(self, order_data: Dict[str, Any]) -> str:
        raise NotImplementedError("Escribir órdenes hacia CSV/Google Sheets no está soportado en esta versión.")
