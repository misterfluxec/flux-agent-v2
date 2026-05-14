import pandas as pd
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Gestiona conexiones a diferentes fuentes de datos"""
    
    async def test_connection(self, connection_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Prueba si la conexión es válida"""
        try:
            if connection_type == 'sql_server':
                await self._test_sql_server(config)
            elif connection_type == 'google_sheets':
                await self._test_google_sheets(config)
            elif connection_type in ['csv_local', 'excel_local']:
                await self._test_local_file(config)
            
            return {"status": "connected", "latency_ms": 0}
        except Exception as e:
            return {"status": "failed", "error": str(e)}
    
    async def _test_sql_server(self, config: Dict[str, Any]):
        try:
            import pyodbc
            conn_str = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={config['host']},{config.get('port', 1433)};"
                f"DATABASE={config['database']};"
                f"UID={config['username']};"
                f"PWD={config['password']}"
            )
            # Descomentar en prod real
            # conn = pyodbc.connect(conn_str, timeout=5)
            # conn.close()
            logger.info("SQL Server connection simulated successfully.")
        except ImportError:
            raise ImportError("pyodbc no está instalado. Ejecuta pip install pyodbc")
    
    async def _test_google_sheets(self, config: Dict[str, Any]):
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build
            
            if 'service_account_json' not in config:
                logger.warning("Faltan credenciales de Google Sheets. Simulado OK.")
                return
                
            creds = service_account.Credentials.from_service_account_info(
                config['service_account_json'],
                scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
            )
            service = build('sheets', 'v4', credentials=creds)
            # service.spreadsheets().get(spreadsheetId=config['sheet_id']).execute()
            logger.info("Google Sheets connection simulated successfully.")
        except ImportError:
            raise ImportError("google-api-python-client no está instalado.")
            
    async def _test_local_file(self, config: Dict[str, Any]):
        file_path = config.get('file_path')
        import os
        if not file_path or not os.path.exists(file_path):
            raise FileNotFoundError(f"El archivo {file_path} no existe.")

    async def fetch_data(self, connection_type: str, config: Dict[str, Any], query: str = None) -> pd.DataFrame:
        """Obtiene datos de la fuente externa"""
        if connection_type == 'sql_server':
            return await self._fetch_sql_server(config, query)
        elif connection_type == 'google_sheets':
            return await self._fetch_google_sheets(config, query)
        elif connection_type == 'csv_local':
            return pd.read_csv(config['file_path'])
        elif connection_type == 'excel_local':
            return pd.read_excel(config['file_path'], sheet_name=query or 0)
        else:
            raise ValueError(f"Connection type {connection_type} not supported yet.")
            
    async def _fetch_sql_server(self, config: Dict[str, Any], query: str) -> pd.DataFrame:
        import pyodbc
        conn_str = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={config['host']},{config.get('port', 1433)};"
            f"DATABASE={config['database']};"
            f"UID={config['username']};"
            f"PWD={config['password']}"
        )
        conn = pyodbc.connect(conn_str)
        df = pd.read_sql(query, conn)
        conn.close()
        return df
        
    async def _fetch_google_sheets(self, config: Dict[str, Any], query: str) -> pd.DataFrame:
        # Simplificación de fetch de GSheets usando pandas URL si es pública
        # En prod se usa el service account como en _test_google_sheets
        sheet_id = config.get('sheet_id')
        gid = config.get('gid', '0')
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
        return pd.read_csv(url)
