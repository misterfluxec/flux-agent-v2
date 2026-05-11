from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from database import obtener_sesion
# from core.event_bus import get_event_bus  # Dependencia hipotética si existe
from connectors.legacy.sqlserver import SQLServerConnector
from connectors.legacy.csv_excel import CSVExcelConnector
from connectors.legacy.connector_sync import SyncEngine
from core.event_bus import EventBus

router = APIRouter(prefix="/api/v1/connectors", tags=["Connectors Layer"])

# Diccionario de adaptadores soportados
ADAPTERS = {
    "sqlserver": SQLServerConnector,
    "csv_excel": CSVExcelConnector
}

def get_connector_instance(tenant_id: str, provider: str, config: Dict[str, Any]):
    adapter_class = ADAPTERS.get(provider.lower())
    if not adapter_class:
        raise HTTPException(status_code=400, detail=f"Provider '{provider}' no soportado. Soportados: {list(ADAPTERS.keys())}")
    return adapter_class(tenant_id=tenant_id, config=config)

@router.post("/{provider}/test")
async def test_connector_connection(
    provider: str, 
    config: Dict[str, Any], 
    db: AsyncSession = Depends(obtener_sesion)
):
    """Prueba la conexión y devuelve las capacidades del ERP / Archivo."""
    tenant_id = config.get('tenant_id')
    if not tenant_id:
        raise HTTPException(status_code=400, detail="tenant_id es requerido en el config")
        
    connector = get_connector_instance(tenant_id, provider, config)
    result = await connector.test_connection()
    return result

@router.post("/{provider}/sync")
async def trigger_sync(
    provider: str,
    config: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(obtener_sesion)
):
    """
    Inicia la sincronización idempotente hacia el Canonical Model.
    Ejecutado en background para no bloquear el Event Loop.
    """
    tenant_id = config.get('tenant_id')
    if not tenant_id:
        raise HTTPException(status_code=400, detail="tenant_id es requerido en el config")
        
    connector = get_connector_instance(tenant_id, provider, config)
    
    # Init event bus (mocked o injectado)
    # event_bus = Depends(get_event_bus) 
    event_bus = None # Pasamos None si no está el bus real importado, el SyncEngine lo tolera
    
    sync_engine = SyncEngine(db, event_bus)
    
    # Delegar a worker de background
    background_tasks.add_task(_run_full_sync, connector, sync_engine, tenant_id)
    
    return {
        "status": "sync_queued", 
        "provider": provider, 
        "message": "Sincronización iniciada en background."
    }

async def _run_full_sync(connector, sync_engine: SyncEngine, tenant_id: str):
    """Función background para ejecutar todo el flujo de sincronización."""
    try:
        # 1. Sync Customers
        if connector.capabilities.get("customers"):
            cust_stats = await sync_engine.sync_customers(tenant_id, connector)
            print(f"[{tenant_id}] Customers Sync: {cust_stats}")
            
        # 2. Sync Products/Inventory
        if connector.capabilities.get("products") or connector.capabilities.get("inventory"):
            prod_stats = await sync_engine.sync_products(tenant_id, connector)
            print(f"[{tenant_id}] Products Sync: {prod_stats}")
            
        # Emitir Sync_Completed event si existe el bus
        if sync_engine.event_bus:
            # event_bus.publish(...)
            pass
            
    except Exception as e:
        print(f"❌ Fallo crítico en background sync [{tenant_id}]: {e}")
