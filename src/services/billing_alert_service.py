from uuid import UUID
from datetime import datetime, timedelta
from domain.usage import BillingAlert, BillingAlertType, UsageResource
from core.event_bus import EventBus
from domain.events import DomainEvent, EventMetadata, EventType, BillingAlertPayload, EmptyPayload

class BillingAlertService:
    THRESHOLDS = [0.8, 1.0, 1.2]
    
    def __init__(self, event_bus: EventBus, redis, db_session_factory):
        self.event_bus = event_bus
        self.redis = redis
        self.db_session_factory = db_session_factory
        self.ALERT_SENT_KEY = "alerts:sent:{tenant}:{resource}:{period}"
    
    async def check_and_alert(self, tenant_id: UUID, resource: UsageResource, consumed: float, limit: float, overage_allowed: bool) -> None:
        if limit <= 0:
            return
            
        ratio = consumed / limit
        period = self._get_period_suffix(resource)
        
        for threshold in self.THRESHOLDS:
            if abs(ratio - threshold) < 0.01 or ratio >= threshold:
                alert_key = self.ALERT_SENT_KEY.format(tenant=tenant_id, resource=resource.value, period=period)
                threshold_str = str(int(threshold * 100))
                specific_alert_key = f"{alert_key}:{threshold_str}"
                
                if await self.redis.get(specific_alert_key):
                    continue
                
                alert_type = self._map_threshold_to_type(threshold)
                alert = BillingAlert(
                    tenant_id=tenant_id,
                    alert_type=alert_type,
                    resource=resource,
                    current_usage=consumed,
                    limit=limit,
                    message=self._build_message(alert_type, resource, consumed, limit),
                    actionable=threshold >= 1.0,
                )
                
                await self.event_bus.publish(DomainEvent(
                    metadata=EventMetadata(
                        event_type=EventType.BILLING_ALERT,
                        tenant_id=tenant_id,
                    ),
                    payload=BillingAlertPayload(
                        alert_id=alert.id,
                        tenant_id=alert.tenant_id,
                        alert_type=alert.alert_type.value,
                        resource=alert.resource.value,
                        current_usage=alert.current_usage,
                        limit=alert.limit,
                        message=alert.message,
                        actionable=alert.actionable,
                        created_at=alert.created_at
                    ),
                ))
                
                # Kill Switch if 100% and no overage allowed
                if threshold >= 1.0 and not overage_allowed:
                    await self._trigger_kill_switch(tenant_id)
                
                await self.redis.setex(specific_alert_key, timedelta(days=31), "1")
    
    async def _trigger_kill_switch(self, tenant_id: UUID):
        """Mecanismo de Desconexión de Emergencia (Kill Switch)"""
        await self.event_bus.publish(DomainEvent(
            metadata=EventMetadata(
                event_type=EventType.TENANT_QUOTA_EXHAUSTED,
                tenant_id=tenant_id,
            ),
            payload=EmptyPayload(),
        ))
    
    def _map_threshold_to_type(self, threshold: float) -> BillingAlertType:
        if threshold < 1.0:
            return BillingAlertType.THRESHOLD_80
        elif threshold == 1.0:
            return BillingAlertType.THRESHOLD_100
        else:
            return BillingAlertType.OVERAGE_CHARGED
    
    def _build_message(self, alert_type: BillingAlertType, resource: UsageResource, consumed: float, limit: float) -> str:
        messages = {
            BillingAlertType.THRESHOLD_80: f"Has usado el 80% de tu quota de {resource.value}.",
            BillingAlertType.THRESHOLD_100: f"Has alcanzado el límite de {resource.value}. Considera upgrade.",
            BillingAlertType.OVERAGE_CHARGED: f"Consumo extra de {resource.value} aplicado con costo adicional.",
        }
        return messages.get(alert_type, "")
    
    def _get_period_suffix(self, resource: UsageResource) -> str:
        now = datetime.utcnow()
        return now.strftime("%Y%m" if resource.period == "month" else "%Y%m%d")
