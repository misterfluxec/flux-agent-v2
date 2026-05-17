import logging
import json
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Dict, Any

from .connection_manager import ConnectionManager

logger = logging.getLogger(__name__)

class SyncEngine:
    """Motor ETL avanzado que ejecuta syncs programadas"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.connection_manager = ConnectionManager()
    
    async def execute_sync(self, session_id: str, tenant_id: str):
        """Ejecuta una sincronización ETL utilizando integration_mappings"""
        # 1. Obtener la sesión de conector y los mappings
        query_session = text("""
            SELECT id, tenant_id, provider as connection_type, session_data as config
            FROM connector_sessions
            WHERE id = :id AND tenant_id = :tenant_id
        """)
        res_session = await self.db.execute(query_session, {"id": session_id, "tenant_id": tenant_id})
        connection = res_session.fetchone()
        
        if not connection:
            raise ValueError(f"Conexión/Sesión {session_id} no encontrada")
            
        # Obtener mapeo is_active para este proveedor
        query_mapping = text("""
            SELECT mapping_rules 
            FROM integration_mappings 
            WHERE tenant_id = :tenant_id AND provider = :provider AND status = 'active'
            LIMIT 1
        """)
        res_mapping = await self.db.execute(query_mapping, {"tenant_id": tenant_id, "provider": connection.connection_type})
        mapping_record = res_mapping.fetchone()
        
        mapping_rules = mapping_record.mapping_rules if mapping_record else {}
        
        # 2. Registrar el inicio del run
        run_query = text("""
            INSERT INTO integration_sync_runs (tenant_id, session_id, sync_type, status)
            VALUES (:tenant_id, :session_id, 'full_etl', 'in_progress')
            RETURNING id
        """)
        res_run = await self.db.execute(run_query, {"tenant_id": tenant_id, "session_id": session_id})
        run_id = res_run.scalar()
        await self.db.commit()
        
        try:
            # 3. Fetch datos externos (Pandas DataFrame)
            config_dict = connection.config if isinstance(connection.config, dict) else json.loads(connection.config)
            df = await self.connection_manager.fetch_data(
                connection.connection_type,
                config_dict,
                query=config_dict.get('query')
            )
            
            rows_fetched = len(df)
            rows_inserted = 0
            rows_updated = 0
            rows_failed = 0
            
            # 4. Transformar y cargar a business_offers
            for _, row in df.iterrows():
                try:
                    action = await self._sync_row_to_catalog(row.to_dict(), mapping_rules, tenant_id)
                    if action == 'insert':
                        rows_inserted += 1
                    elif action == 'update':
                        rows_updated += 1
                except Exception as e:
                    rows_failed += 1
                    logger.error(f"Error syncing row: {e}")
            
            # 5. Finalizar log
            status = 'completed' if rows_failed == 0 else 'partial'
            details = {
                "rows_fetched": rows_fetched,
                "rows_inserted": rows_inserted,
                "rows_updated": rows_updated,
                "rows_failed": rows_failed
            }
            
            finish_run_query = text("""
                UPDATE integration_sync_runs 
                SET status = :status, details = :details, completed_at = NOW()
                WHERE id = :run_id
            """)
            await self.db.execute(finish_run_query, {
                "status": status, 
                "details": json.dumps(details), 
                "run_id": run_id
            })
            await self.db.commit()
            
        except Exception as e:
            error_query = text("""
                UPDATE integration_sync_runs 
                SET status = 'failed', error_message = :error, completed_at = NOW()
                WHERE id = :run_id
            """)
            await self.db.execute(error_query, {"error": str(e)[:500], "run_id": run_id})
            await self.db.commit()
            raise
            
    async def _sync_row_to_catalog(self, row: Dict, mapping_rules: Dict, tenant_id: str) -> str:
        """Aplica transformaciones y hace upsert en business_offers."""
        transformed = {}
        
        # El mapping rules puede ser una lista de reglas
        # Ejemplo: [{"external": "sku", "canonical": "name", "rule": "uppercase"}, ...]
        if isinstance(mapping_rules, list):
            rules = mapping_rules
        else:
            # Soporte legacy
            rules = [{"external": k, "canonical": v, "rule": None} for k, v in mapping_rules.items()]
            
        for mapping in rules:
            ext_field = mapping.get('external')
            can_field = mapping.get('canonical')
            rule = mapping.get('rule')
            
            if ext_field in row:
                transformed[can_field] = self._apply_transformation(row[ext_field], rule)
                
        # Upsert
        # Identificador principal es 'name' o un external_id (si existiera)
        identifier = transformed.get('name', 'Unknown')
        
        check_query = text("""
            SELECT id FROM business_offers 
            WHERE tenant_id = :tenant_id AND name = :name
        """)
        res = await self.db.execute(check_query, {"tenant_id": tenant_id, "name": identifier})
        existing_id = res.scalar()
        
        if existing_id:
            # Update
            update_fields = []
            params = {"id": existing_id, "tenant_id": tenant_id}
            for k, v in transformed.items():
                if k != 'name':
                    update_fields.append(f"{k} = :{k}")
                    params[k] = v
                    
            if update_fields:
                update_query = text(f"""
                    UPDATE business_offers 
                    SET {', '.join(update_fields)}, updated_at = NOW()
                    WHERE id = :id AND tenant_id = :tenant_id
                """)
                await self.db.execute(update_query, params)
            return 'update'
        else:
            # Insert
            fields = ["tenant_id", "type"]
            values = [":tenant_id", "'physical_product'"]
            params = {"tenant_id": tenant_id}
            
            for k, v in transformed.items():
                fields.append(k)
                values.append(f":{k}")
                params[k] = v
                
            insert_query = text(f"""
                INSERT INTO business_offers ({', '.join(fields)})
                VALUES ({', '.join(values)})
            """)
            await self.db.execute(insert_query, params)
            return 'insert'
            
    def _apply_transformation(self, value: Any, rule: str) -> Any:
        if not rule or value is None:
            return value
            
        try:
            if rule == 'uppercase':
                return str(value).upper()
            elif rule == 'lowercase':
                return str(value).lower()
            elif rule == 'trim':
                return str(value).strip()
            elif rule.startswith('multiply_'):
                factor = float(rule.split('_')[1])
                return float(value) * factor
        except Exception:
            pass
            
        return value
