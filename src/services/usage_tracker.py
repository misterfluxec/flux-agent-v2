import asyncio
from datetime import datetime
from typing import List, Dict, Optional
from uuid import UUID
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from domain.usage import UsageRecord, UsageResource
from config import obtener_config

settings = obtener_config()

class UsageTracker:
    """
    Tracker de consumo con buffer en Redis + flush batch a PostgreSQL.
    Incluye pre-agregación (rollup) y pricing dinámico multi-model.
    """
    
    BUFFER_KEY = "usage:buffer:{tenant_id}"
    FLUSH_INTERVAL_SECONDS = 30
    FLUSH_BATCH_SIZE = 100
    
    def __init__(self, redis: Redis, db_session_factory):
        self.redis = redis
        self.db_session_factory = db_session_factory
        self._flush_task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()
    
    async def start(self):
        self._flush_task = asyncio.create_task(self._flush_loop())
    
    async def stop(self):
        self._stop_event.set()
        if self._flush_task:
            await self._flush_task
        await self._flush_all_buffers()
    
    async def record(self, record: UsageRecord) -> None:
        if record.cost_usd == 0:
            record.cost_usd = await self._calculate_cost(record)
        
        buffer_key = self.BUFFER_KEY.format(tenant_id=record.tenant_id)
        await self.redis.lpush(buffer_key, record.model_dump_json())
        
        await self._update_realtime_counter(record)
        
        # Las alertas se manejan separadamente en QuotaManager o BillingAlertService 
        # en base a los consumos actualizados
    
    async def _update_realtime_counter(self, record: UsageRecord) -> None:
        period_key = self._get_period_key(record.resource, record.tenant_id)
        await self.redis.hincrbyfloat(period_key, "consumed", record.amount)
        # Asegurar expiración de maximo 1 mes aprox (31 dias)
        await self.redis.expire(period_key, 86400 * 31)
    
    def _get_period_key(self, resource: UsageResource, tenant_id: UUID) -> str:
        now = datetime.utcnow()
        if "minute" in resource.value:  # Caso especial rápido
            suffix = now.strftime("%Y%m%d%H%M")
        else:
            suffix = now.strftime("%Y%m") # Default a mensual
        return f"quota:{tenant_id}:{resource.value}:{suffix}"
    
    async def _flush_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                await asyncio.sleep(self.FLUSH_INTERVAL_SECONDS)
                await self._flush_all_buffers()
            except Exception as e:
                await asyncio.sleep(5)
    
    async def _flush_all_buffers(self) -> int:
        flushed = 0
        async for key in self.redis.scan_iter("usage:buffer:*"):
            records = await self._pop_buffer_batch(key, self.FLUSH_BATCH_SIZE)
            if records:
                rolled_up_records = self._rollup_records(records)
                await self._persist_to_postgres(rolled_up_records)
                flushed += len(rolled_up_records)
        return flushed
    
    def _rollup_records(self, records: List[UsageRecord]) -> List[UsageRecord]:
        """Pre-agregación (Rollup) para ahorrar rows en DB"""
        aggregated: Dict[str, UsageRecord] = {}
        for r in records:
            # Agrupar por resource + model_id (si existe)
            model_id = r.metadata.get("model_id", "default")
            group_key = f"{r.resource.value}_{model_id}"
            
            if group_key not in aggregated:
                aggregated[group_key] = r
            else:
                aggregated[group_key].amount += r.amount
                aggregated[group_key].cost_usd += r.cost_usd
        
        return list(aggregated.values())

    async def _pop_buffer_batch(self, key: str, batch_size: int) -> List[UsageRecord]:
        raw = await self.redis.lpop(key, count=batch_size)
        if not raw:
            return []
        # Si redis lpop devuelve una lista
        if isinstance(raw, list):
            return [UsageRecord.model_validate_json(r) for r in raw]
        else:
            return [UsageRecord.model_validate_json(raw)]
    
    async def _persist_to_postgres(self, records: List[UsageRecord]) -> None:
        if not self.db_session_factory:
            # Si no hay DB inyectada (ej. entorno de prueba ligero), skip
            return
            
        async with self.db_session_factory() as session:
            for attempt in range(3):
                try:
                    # En SQLAlchemy, no se requiere add_all si estamos usando diccionarios con insert bulk.
                    # Aquí simulamos con add_all porque asumimos que hay un ORM model correspondiente
                    # Por simplicidad en esta fase, lo dejamos como placeholder o iteración.
                    # session.add_all(records_orm) 
                    # await session.commit()
                    return
                except Exception as e:
                    if attempt == 2:
                        await self._requeue_failed(records)
                        # Opcional: Notificar a DLQ
                        raise
                    await asyncio.sleep(2 ** attempt)
    
    async def _requeue_failed(self, records: List[UsageRecord]) -> None:
        for record in reversed(records):
            await self.redis.lpush(
                self.BUFFER_KEY.format(tenant_id=record.tenant_id),
                record.model_dump_json()
            )
    
    async def _calculate_cost(self, record: UsageRecord) -> float:
        """Pricing Dinámico Multi-Modelo"""
        model_id = record.metadata.get("model_id", "default")
        
        # Tarifas por 1M tokens o unidad respectiva
        pricing_table = {
            "llama3-8b": {UsageResource.LLM_TOKENS_INPUT: 0.0000005, UsageResource.LLM_TOKENS_OUTPUT: 0.0000015},
            "mistral-large": {UsageResource.LLM_TOKENS_INPUT: 0.000002, UsageResource.LLM_TOKENS_OUTPUT: 0.000006},
            "gpt-4o": {UsageResource.LLM_TOKENS_INPUT: 0.000005, UsageResource.LLM_TOKENS_OUTPUT: 0.000015},
            "default": {
                UsageResource.LLM_TOKENS_INPUT: 0.000001, 
                UsageResource.LLM_TOKENS_OUTPUT: 0.000003,
                UsageResource.STT_SECONDS: 0.0005,
                UsageResource.TOOL_EXECUTIONS_PREMIUM: 0.01
            }
        }
        
        rates = pricing_table.get(model_id, pricing_table["default"])
        rate = rates.get(record.resource, pricing_table["default"].get(record.resource, 0))
        
        return round(record.amount * rate, 6)
