import hashlib
import json
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime

from connectors.v2.base_connector import BaseDataConnector

class GoogleSheetsCSVConnector(BaseDataConnector):
    """
    V2 Architecture: PURE DATA EXTRACTOR for Sheets & CSV.
    Refinements:
    - Schema Fingerprint (Detección de alteración de Excel).
    - Enriched Dry Run (Validación empresarial de datos previa).
    - Sync Modes Soportados: full, incremental, manual.
    """
    
    def __init__(self, config_encrypted: Dict[str, Any]):
        super().__init__(config_encrypted)
        self.source_type = self.config.get('source_type', 'url')
        self.url = self.config.get('url')
        self.file_path = self.config.get('file_path')
        self.delimiter = self.config.get('delimiter', ',')
        
    def _read_dataframe(self) -> pd.DataFrame:
        try:
            if self.source_type == 'url' and self.url:
                if 'csv' in self.url.lower():
                    return pd.read_csv(self.url)
                else:
                    return pd.read_excel(self.url)
            elif self.source_type == 'file' and self.file_path:
                if self.file_path.endswith('.csv'):
                    return pd.read_csv(self.file_path, delimiter=self.delimiter)
                else:
                    return pd.read_excel(self.file_path)
            raise ValueError("Fuente no configurada o inválida.")
        except Exception as e:
            raise Exception(f"Error leyendo la fuente de datos: {e}")

    def generate_schema_fingerprint(self, columns: List[str]) -> str:
        """
        Genera un hash MD5 de la estructura exacta de las columnas.
        Si el usuario renombra una columna en su Excel, el hash cambiará
        y el sistema detendrá la sincronización para evitar corrupción.
        """
        normalized_cols = [str(c).strip().lower() for c in columns]
        return hashlib.md5(json.dumps(normalized_cols).encode('utf-8')).hexdigest()

    async def connect(self) -> bool:
        try:
            df = self._read_dataframe()
            return not df.empty
        except Exception:
            return False

    async def fetch_raw_data(self, entity_name: str, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        df = self._read_dataframe()
        
        # Validar Fingerprint contra el config (si existe)
        expected_fingerprint = self.config.get('expected_schema_fingerprint')
        if expected_fingerprint:
            current_fingerprint = self.generate_schema_fingerprint(list(df.columns))
            if current_fingerprint != expected_fingerprint:
                raise ValueError("SCHEMA_ALTERED: La estructura del archivo ha cambiado drásticamente. Revise el mapeo.")

        updated_column = self.config.get('updated_at_column', 'updated_at')
        if since and updated_column in df.columns:
            df[updated_column] = pd.to_datetime(df[updated_column], errors='coerce')
            df = df[df[updated_column] > pd.Timestamp(since)]
            
        df = df.replace({np.nan: None})
        
        return df.to_dict(orient='records')

    async def validate_schema(self, expected_columns: List[str], pk_column: str, numeric_columns: List[str] = None) -> Dict[str, Any]:
        """
        ENRICHED DRY RUN MODE:
        Realiza validaciones defensivas profundas antes de intentar la carga.
        """
        numeric_columns = numeric_columns or []
        try:
            df = self._read_dataframe()
            actual_columns = list(df.columns)
            
            # 1. Columnas faltantes
            missing = [col for col in expected_columns if col not in actual_columns]
            
            errors = []
            warnings = []
            
            # 2. Validación de PK (Duplicados o Nulos)
            if pk_column in df.columns:
                null_pks = df[pk_column].isnull().sum()
                if null_pks > 0:
                    errors.append(f"Se encontraron {null_pks} filas sin identificador único ({pk_column}).")
                
                duplicates = df[pk_column].duplicated().sum()
                if duplicates > 0:
                    errors.append(f"Se encontraron {duplicates} identificadores duplicados en {pk_column}.")
            
            # 3. Validación Numérica (Negativos o Tipos incorrectos)
            for num_col in numeric_columns:
                if num_col in df.columns:
                    # Intentar convertir a numérico
                    df[num_col] = pd.to_numeric(df[num_col], errors='coerce')
                    invalid_types = df[num_col].isnull().sum()
                    if invalid_types > 0:
                        warnings.append(f"La columna {num_col} contiene {invalid_types} valores no numéricos o vacíos.")
                    
                    if pd.api.types.is_numeric_dtype(df[num_col]):
                        negatives = (df[num_col] < 0).sum()
                        if negatives > 0:
                            errors.append(f"La columna {num_col} tiene {negatives} valores negativos (prohibido).")

            is_valid = len(missing) == 0 and len(errors) == 0
            
            return {
                "valid": is_valid,
                "current_schema_fingerprint": self.generate_schema_fingerprint(actual_columns),
                "total_rows": len(df),
                "actual_columns": actual_columns,
                "missing_columns": missing,
                "validation_errors": errors,
                "validation_warnings": warnings,
                "preview_sample": df.head(3).replace({np.nan: None}).to_dict(orient='records')
            }
        except Exception as e:
            return {
                "valid": False,
                "validation_errors": [str(e)]
            }
