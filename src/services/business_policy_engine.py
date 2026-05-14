from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models import BusinessPolicy, PolicyLog
import json

class BusinessPolicyEngine:
    """
    Evaluates dynamic business policies (Business Rules) triggered by events.
    Replaces hardcoded logic for discounts, approvals, or routing.
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def evaluate(self, tenant_id: str, event_type: str, aggregate_id: str, context: Dict[str, Any]) -> List[Dict]:
        """
        Evaluates active policies for a specific event.
        Returns a list of actions the system must perform.
        """
        stmt = select(BusinessPolicy).where(
            BusinessPolicy.tenant_id == tenant_id,
            BusinessPolicy.trigger_event == event_type,
            BusinessPolicy.is_active == True
        ).order_by(BusinessPolicy.priority.desc())
        
        result = await self.db.execute(stmt)
        policies = result.scalars().all()
        
        actions = []

        for policy in policies:
            condition_met = await self._check_condition(policy, context)
            
            await self._log_policy_execution(policy.id, tenant_id, aggregate_id, context, condition_met)

            if condition_met:
                actions.append({
                    "policy_id": str(policy.id),
                    "action": policy.action_type,
                    "payload": policy.action_payload,
                    "reason": policy.condition_type
                })
        
        return actions

    async def _check_condition(self, policy: BusinessPolicy, context: Dict) -> bool:
        """Safe evaluation of conditions"""
        if policy.condition_type == 'always':
            return True
            
        if policy.condition_type == 'amount_threshold':
            val = context.get('total_amount', 0)
            threshold = policy.condition_value
            return float(val) > float(threshold)
            
        return False

    async def _log_policy_execution(self, policy_id, tenant_id, agg_id, context, result_bool):
        """Append-only audit trail for compliance"""
        log = PolicyLog(
            policy_id=policy_id,
            tenant_id=tenant_id,
            aggregate_id=agg_id,
            aggregate_type=context.get('type', 'unknown'),
            trigger_data=context,
            result='applied' if result_bool else 'bypassed'
        )
        self.db.add(log)
