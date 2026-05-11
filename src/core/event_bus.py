import json
import asyncio
from datetime import datetime
from typing import Callable, Any
from redis.asyncio import Redis
from pydantic import ValidationError

from domain.events import DomainEvent, EventType, EventMetadata
from config import obtener_config

settings = obtener_config()


class EventBus:
    """
    Event Bus basado en Redis Streams.
    
    - Publica eventos a streams por tenant
    - Permite suscripción por tipo de evento
    - Soporta replay desde un timestamp o ID
    - Dead Letter Queue para eventos fallidos
    """
    
    STREAM_GLOBAL = "fluxagent:events:global"
    STREAM_TENANT_TEMPLATE = "fluxagent:events:tenant:{tenant_id}"
    STREAM_DLQ = "fluxagent:events:dlq"
    CONSUMER_GROUP = "fluxagent:processors"
    
    def __init__(self, redis: Redis):
        self.redis = redis
        self._subscribers: dict[EventType, list[Callable]] = {}
        self._tasks: list[asyncio.Task] = []          # Rastreo de consumers
        self._stop_event = asyncio.Event()            # Señal de apagado limpio
    
    async def publish(self, event: DomainEvent) -> str:
        """
        Publica un evento en los streams correspondientes.
        
        Returns:
            event_id: El ID del evento en Redis Streams para tracking
        """
        stream_data = event.to_redis_stream()
        
        # Determine dynamic MAXLEN based on severity
        severity = event.metadata.severity
        if severity == "critical":
            dynamic_maxlen = 15000
        elif severity == "high":
            dynamic_maxlen = 10000
        elif severity == "medium":
            dynamic_maxlen = 5000
        else:
            dynamic_maxlen = 2000
        
        # Publicar en stream global
        global_id = await self.redis.xadd(
            self.STREAM_GLOBAL,
            stream_data,
            maxlen=dynamic_maxlen,
            approximate=True,
        )
        
        # Publicar en stream del tenant
        tenant_stream = self.STREAM_TENANT_TEMPLATE.format(
            tenant_id=event.metadata.tenant_id
        )
        await self.redis.xadd(
            tenant_stream,
            stream_data,
            maxlen=dynamic_maxlen,
            approximate=True,
        )
        
        # Establecer TTL agresivo (4 horas = 14400 segundos) para evitar memory leak
        await self.redis.expire(self.STREAM_GLOBAL, 14400)
        await self.redis.expire(tenant_stream, 14400)
        
        await self._log_event_published(event, global_id)
        
        return global_id
    
    async def subscribe(
        self,
        event_types: list[EventType],
        handler: Callable[[DomainEvent], Any],
        consumer_name: str,
        tenant_id: str | None = None,
    ) -> None:
        """
        Registra un handler para procesar eventos de tipos específicos.
        """
        stream = (
            self.STREAM_TENANT_TEMPLATE.format(tenant_id=tenant_id)
            if tenant_id
            else self.STREAM_GLOBAL
        )
        
        try:
            await self.redis.xgroup_create(
                stream, self.CONSUMER_GROUP, id="0", mkstream=True
            )
        except Exception:
            pass
        
        for event_type in event_types:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            self._subscribers[event_type].append(handler)
        
        # Guardar referencia de la tarea para shutdown seguro
        task = asyncio.create_task(
            self._consume_stream(stream, consumer_name, event_types, handler)
        )
        self._tasks.append(task)
    
    async def _consume_stream(
        self,
        stream: str,
        consumer_name: str,
        event_types: list[EventType],
        handler: Callable[[DomainEvent], Any],
    ) -> None:
        """
        Loop infinito para consumir eventos del stream.
        """
        while not self._stop_event.is_set():
            try:
                messages = await self.redis.xreadgroup(
                    groupname=self.CONSUMER_GROUP,
                    consumername=consumer_name,
                    streams={stream: ">"},
                    count=10,
                    block=5000,
                )
                
                if not messages:
                    continue
                
                for stream_name, stream_messages in messages:
                    for message_id, message_data in stream_messages:
                        try:
                            event_data = json.loads(message_data[b"data"].decode())
                            event = DomainEvent.model_validate(event_data)
                            
                            if event.metadata.event_type not in event_types:
                                continue
                            
                            await handler(event)
                            await self.redis.xack(stream, self.CONSUMER_GROUP, message_id)
                            
                        except ValidationError as e:
                            await self._move_to_dlq(stream, message_id, message_data, "validation_error", str(e))
                            await self.redis.xack(stream, self.CONSUMER_GROUP, message_id)
                            
                        except Exception as e:
                            await self._handle_processing_error(stream, message_id, message_data, e)
                            
            except asyncio.CancelledError:
                break
            except Exception as e:
                await asyncio.sleep(5)
                continue
    
    async def _handle_processing_error(
        self, stream: str, message_id: str, message_data: dict, error: Exception
    ) -> None:
        """
        Maneja errores de procesamiento con retry exponencial.
        """
        retry_key = f"event:retry:{message_id}"
        retries = await self.redis.incr(retry_key)
        
        if retries <= settings.max_event_retries:
            backoff = min(2 ** retries, 60)
            await asyncio.sleep(backoff)
            await self.redis.xadd(stream, message_data, id=message_id)
        else:
            await self._move_to_dlq(stream, message_id, message_data, "processing_error", str(error))
            await self.redis.xack(stream, self.CONSUMER_GROUP, message_id)
            await self.redis.delete(retry_key)
    
    async def _move_to_dlq(
        self, original_stream: str, message_id: str, message_data: dict, error_type: str, error_msg: str
    ) -> None:
        """Mueve un evento fallido a la Dead Letter Queue"""
        dlq_data = {
            **message_data,
            "error_type": error_type,
            "error_message": error_msg,
            "original_stream": original_stream,
            "original_message_id": message_id,
            "failed_at": datetime.utcnow().isoformat(),
        }
        await self.redis.xadd(self.STREAM_DLQ, dlq_data, maxlen=10000, approximate=True)
    
    async def _log_event_published(self, event: DomainEvent, event_id: str) -> None:
        pass
    
    async def replay_events(
        self,
        event_types: list[EventType],
        handler: Callable[[DomainEvent], Any],
        start_from: str | datetime = "0",
        tenant_id: str | None = None,
    ) -> int:
        stream = (
            self.STREAM_TENANT_TEMPLATE.format(tenant_id=tenant_id)
            if tenant_id
            else self.STREAM_GLOBAL
        )
        
        processed = 0
        start_id = start_from if isinstance(start_from, str) else "0"
        
        while True:
            messages = await self.redis.xrange(stream, min=start_id, count=100)
            if not messages:
                break
            
            for message_id, message_data in messages:
                try:
                    event_data = json.loads(message_data[b"data"].decode())
                    event = DomainEvent.model_validate(event_data)
                    
                    if event.metadata.event_type in event_types:
                        await handler(event)
                        processed += 1
                    
                    start_id = message_id
                    
                except Exception:
                    start_id = message_id
                    continue
            
            if len(messages) < 100:
                break
        
        return processed

    async def close(self) -> None:
        """Apagado seguro: espera a que terminen los eventos en proceso"""
        self._stop_event.set()
        
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
            
        await self.redis.close()
