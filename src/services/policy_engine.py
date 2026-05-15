import json
import logging
import uuid
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from redis.asyncio import Redis

from domain.policies import PolicyRule, PolicyEvaluationRequest, PolicyEvaluationResult, PolicyEngineOutput, PolicyAction

logger = logging.getLogger("flux.policy_engine")

class PolicyEngine:
    def __init__(self, redis: Redis, db: AsyncSession):
        self.redis = redis
        self.db = db
        self._cache: dict[str, list[PolicyRule]] = {}

    async def create_rule(self, rule: PolicyRule,
                          tenant_id: str | None = None) -> None:
        await self.db.execute(
            text("""
                INSERT INTO flux_policies
                  (id, tenant_id, name, description, conditions,
                   action, priority, enabled, tenant_plans,
                   industries, tools, modifications)
                VALUES
                  (:id, :tid, :name, :desc, :conds::jsonb,
                   :action, :priority, :enabled,
                   :plans::jsonb, :industries::jsonb,
                   :tools::jsonb, :mods::jsonb)
                ON CONFLICT (id) DO NOTHING
            """),
            {
                "id": str(rule.id),
                "tid": tenant_id,
                "name": rule.name,
                "desc": rule.description,
                "conds": json.dumps([
                    {"field": c.field,
                     "operator": c.operator.value,
                     "value": c.value}
                    for c in rule.conditions
                ]),
                "action": rule.action.value,
                "priority": rule.priority,
                "enabled": rule.enabled,
                "plans": json.dumps(rule.tenant_plans or []),
                "industries": json.dumps(rule.industries or []),
                "tools": json.dumps(rule.tools)
                         if rule.tools is not None else None,
                "mods": json.dumps(rule.modifications or {}),
            },
        )
        await self.db.commit()
        self._cache.pop(tenant_id or "global", None)

    async def _get_applicable_rules(
        self, tenant_id: str, tool_name: str
    ) -> list[PolicyRule]:
        from domain.policies import PolicyCondition, PolicyOperator

        cache_key = f"{tenant_id}:{tool_name}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        result = await self.db.execute(
            text("""
                SELECT id, name, description, conditions,
                       action, priority, enabled,
                       tenant_plans, industries,
                       tools, modifications
                FROM flux_policies
                WHERE enabled = TRUE
                  AND (tenant_id IS NULL
                       OR tenant_id = :tid::uuid)
                  AND (tools IS NULL
                       OR tools @> :tool_filter::jsonb)
                ORDER BY priority DESC
            """),
            {
                "tid": tenant_id,
                "tool_filter": json.dumps([tool_name]),
            },
        )
        rows = result.fetchall()

        rules: list[PolicyRule] = []
        for r in rows:
            try:
                conds = [
                    PolicyCondition(
                        field=c["field"],
                        operator=PolicyOperator(c["operator"]),
                        value=c["value"],
                    )
                    for c in (r.conditions or [])
                ]
                rules.append(PolicyRule(
                    id=r.id,
                    name=r.name,
                    description=r.description or "",
                    conditions=conds,
                    action=PolicyAction(r.action),
                    priority=r.priority,
                    enabled=r.enabled,
                    tenant_plans=r.tenant_plans or [],
                    industries=r.industries or [],
                    tools=r.tools,
                    modifications=r.modifications or {},
                ))
            except Exception as e:
                logger.warning(
                    "policy_rule_deserialize_error",
                    extra={"rule_name": r.name, "error": str(e)}
                )

        if not rules:
            rules = [PolicyRule(
                id=str(uuid.uuid4()),
                name="default-allow",
                description="Permiso por defecto (sin reglas en DB)",
                conditions=[],
                action=PolicyAction.ALLOW,
                priority=0,
                enabled=True,
                tenant_plans=["basic", "pro", "enterprise"],
            )]

        self._cache[cache_key] = rules
        return rules

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

    async def _log_evaluation(
        self,
        request: PolicyEvaluationRequest,
        evaluations: List[PolicyEvaluationResult],
        final_decision: str,
    ) -> str:
        audit_id = str(uuid.uuid4())
        try:
            await self.db.execute(
                text("""
                    INSERT INTO flux_policy_audit_log
                      (id, tenant_id, tool_name,
                       final_decision, evaluations)
                    VALUES
                      (:id, :tid::uuid, :tool,
                       :decision, :evals::jsonb)
                """),
                {
                    "id": audit_id,
                    "tid": str(request.tenant_id),
                    "tool": request.tool_name,
                    "decision": final_decision,
                    "evals": json.dumps([
                        {
                            "rule_id": str(e.rule_id),
                            "rule_name": e.rule_name,
                            "matched": e.matched,
                            "action": e.action.value
                                if hasattr(e.action, "value")
                                else str(e.action),
                            "decision": e.decision,
                            "reason": e.reason,
                        }
                        for e in evaluations
                    ]),
                },
            )
            await self.db.commit()
        except Exception as exc:
            logger.warning("policy_audit_log_failed",
                          extra={"error": str(exc)})
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
