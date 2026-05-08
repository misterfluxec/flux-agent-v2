import uuid
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from src.domain.policies import PolicyRule, PolicyEvaluationRequest, PolicyEvaluationResult, PolicyEngineOutput, PolicyAction

class PolicyEngine:
    def __init__(self, redis: Redis, db: AsyncSession):
        self.redis = redis
        self.db = db
        # In a real app, this would be an LRU cache or fetched from DB
        self._rules_cache: List[PolicyRule] = []

    async def create_rule(self, rule: PolicyRule):
        """Para pruebas y scaffolding. En prod, esto va a DB."""
        self._rules_cache.append(rule)

    async def _get_applicable_rules(self, tenant_id: str, tool_name: str) -> List[PolicyRule]:
        # En prod: SELECT * FROM policies WHERE tenant_id = tenant_id AND (tools IS NULL OR tool_name = ANY(tools))
        # Por ahora usamos la cache de prueba
        applicable = []
        for r in self._rules_cache:
            if not r.enabled:
                continue
            if r.tools is not None and tool_name not in r.tools:
                continue
            applicable.append(r)
        return applicable

    def _map_action_to_decision(self, action: PolicyAction) -> str:
        if action == PolicyAction.ALLOW:
            return "allowed"
        elif action == PolicyAction.DENY:
            return "denied"
        elif action == PolicyAction.REQUIRE_APPROVAL:
            return "pending_approval"
        elif action == PolicyAction.MODIFY:
            return "modified"
        return "allowed"

    async def _log_evaluation(self, request: PolicyEvaluationRequest, evaluations: List[PolicyEvaluationResult], final_decision: str) -> str:
        audit_id = str(uuid.uuid4())
        # En prod: Insertar log asíncrono o empujar al Event Bus
        return audit_id

    async def evaluate_tool_execution(self, request: PolicyEvaluationRequest) -> PolicyEngineOutput:
        # 1. Cargar reglas habilitadas para este tenant/tool
        rules = await self._get_applicable_rules(str(request.tenant_id), request.tool_name)
        
        evaluations = []
        final_decision = "allowed"
        applied_mods = {}
        
        # 2. Evaluar en orden de prioridad
        for rule in sorted(rules, key=lambda r: r.priority, reverse=True):
            if all(cond.evaluate(request.context) for cond in rule.conditions):
                result = PolicyEvaluationResult(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    matched=True,
                    action=rule.action,
                    decision=self._map_action_to_decision(rule.action),
                    reason=rule.description,
                    modifications_applied=rule.modifications if rule.action == PolicyAction.MODIFY else None,
                )
                evaluations.append(result)
                
                if rule.action == PolicyAction.DENY:
                    final_decision = "denied"
                    break  # Deny es terminal
                elif rule.action == PolicyAction.MODIFY:
                    applied_mods.update(rule.modifications)
                elif rule.action == PolicyAction.REQUIRE_APPROVAL:
                    final_decision = "pending_approval"
        
        # 3. Registrar en audit log (asíncrono, no bloqueante)
        audit_id = await self._log_evaluation(request, evaluations, final_decision)
        
        return PolicyEngineOutput(
            allowed=final_decision in ["allowed", "modified"],
            requires_approval=final_decision == "pending_approval",
            evaluations=evaluations,
            final_decision=final_decision,
            applied_modifications=applied_mods,
            audit_log_entry_id=audit_id,
        )
