from __future__ import annotations
import logging
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from domain.workflow_schemas import (
    WorkflowDefinition, NodeDefinition,
    WorkflowRunStatus, StepRunStatus, WorkflowActionType,
)
from services.workflow.step_executor import (
    StepExecutorFactory, StepExecutionResult,
)
from core.exceptions import ResourceNotFoundError, BusinessRuleError

logger = logging.getLogger("flux.workflow_engine")

MAX_STEPS_PER_RUN = 100  # circuit breaker anti-loop

class WorkflowRuntimeEngine:

    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.executor_factory = StepExecutorFactory()

    async def execute_run(self, run_id: UUID) -> None:
        run = await self._get_run(run_id)
        if not run:
            raise ResourceNotFoundError(
                f"WorkflowRun {run_id} no encontrado"
            )

        if run["status"] in (
            WorkflowRunStatus.COMPLETED,
            WorkflowRunStatus.FAILED,
            WorkflowRunStatus.CANCELLED,
        ):
            logger.info("workflow_run_already_terminal",
                       extra={"run_id": str(run_id),
                              "status": run["status"]})
            return

        definition = await self._get_definition(
            run["workflow_definition_id"]
        )
        context: dict[str, Any] = run["context"] or {}
        current_node_id: str = (
            run["current_node_id"] or definition.start_node_id
        )

        logger.info("workflow_run_start",
                   extra={"run_id": str(run_id),
                          "node": current_node_id})

        steps_executed = 0
        while current_node_id and steps_executed < MAX_STEPS_PER_RUN:
            node = self._get_node(definition, current_node_id)
            if not node:
                await self._mark_failed(
                    run_id,
                    f"Nodo '{current_node_id}' no encontrado en definición"
                )
                return

            step_run_id = await self._create_step_run(
                run_id, node, context
            )
            steps_executed += 1

            try:
                executor = self.executor_factory.get_executor(
                    node.type
                )
                result: StepExecutionResult = await executor.execute(
                    node, context
                )
            except Exception as exc:
                await self._complete_step_run(
                    step_run_id,
                    StepRunStatus.FAILED,
                    error=str(exc),
                )
                await self._mark_failed(run_id, str(exc))
                logger.exception("workflow_step_error",
                               extra={"run_id": str(run_id),
                                      "node": current_node_id})
                return

            await self._complete_step_run(
                step_run_id, result.status,
                output=result.output,
                error=result.error_message,
            )

            if result.status == StepRunStatus.SUSPENDED:
                context[f"steps.{node.id}.output"] = result.output
                await self._save_context(run_id, context,
                                         current_node_id)
                await self._mark_suspended(
                    run_id, current_node_id
                )
                logger.info("workflow_run_suspended",
                           extra={"run_id": str(run_id),
                                  "node": current_node_id})
                return

            if result.status == StepRunStatus.FAILED:
                await self._mark_failed(
                    run_id,
                    result.error_message or "Step falló"
                )
                return

            context[f"steps.{node.id}.output"] = result.output
            await self._save_context(run_id, context,
                                      result.next_node_id or "")
            current_node_id = result.next_node_id or ""

        if steps_executed >= MAX_STEPS_PER_RUN:
            await self._mark_failed(
                run_id, f"Límite de {MAX_STEPS_PER_RUN} pasos alcanzado"
            )
            return

        await self._mark_completed(run_id)
        logger.info("workflow_run_completed",
                   extra={"run_id": str(run_id),
                          "steps": steps_executed})

    async def _get_run(self, run_id: UUID) -> dict | None:
        r = await self.db.execute(
            text("""
                SELECT id, status, workflow_definition_id,
                       current_node_id, context
                FROM flux_workflow_runs
                WHERE id = :rid
            """),
            {"rid": str(run_id)},
        )
        row = r.fetchone()
        if not row:
            return None
        return {
            "id": row.id,
            "status": row.status,
            "workflow_definition_id": row.workflow_definition_id,
            "current_node_id": row.current_node_id,
            "context": row.context or {},
        }

    async def _get_definition(
        self, definition_id: str
    ) -> WorkflowDefinition:
        r = await self.db.execute(
            text("""
                SELECT definition FROM flux_workflow_definitions
                WHERE id = :did AND is_active = TRUE
            """),
            {"did": str(definition_id)},
        )
        row = r.fetchone()
        if not row:
            raise ResourceNotFoundError(
                f"WorkflowDefinition {definition_id} no encontrada"
            )
        return WorkflowDefinition(**row.definition)

    def _get_node(
        self, definition: WorkflowDefinition, node_id: str
    ) -> NodeDefinition | None:
        for node in definition.nodes:
            if node.id == node_id:
                return node
        return None

    async def _create_step_run(
        self,
        run_id: UUID,
        node: NodeDefinition,
        context: dict,
    ) -> UUID:
        step_id = uuid4()
        await self.db.execute(
            text("""
                INSERT INTO flux_workflow_step_runs
                  (id, run_id, node_id, node_type,
                   status, input_snapshot)
                VALUES
                  (:id, :run_id, :node_id, :node_type,
                   'running', :snapshot::jsonb)
            """),
            {
                "id": str(step_id),
                "run_id": str(run_id),
                "node_id": node.id,
                "node_type": node.type.value,
                "snapshot": __import__("json").dumps(context),
            },
        )
        await self.db.commit()
        return step_id

    async def _complete_step_run(
        self,
        step_run_id: UUID,
        status: StepRunStatus,
        output: dict | None = None,
        error: str | None = None,
    ) -> None:
        import json
        await self.db.execute(
            text("""
                UPDATE flux_workflow_step_runs
                SET status = :status,
                    output = :output::jsonb,
                    error_message = :error,
                    completed_at = NOW()
                WHERE id = :sid
            """),
            {
                "sid": str(step_run_id),
                "status": status.value,
                "output": json.dumps(output or {}),
                "error": error,
            },
        )
        await self.db.commit()

    async def _save_context(
        self, run_id: UUID, context: dict, current_node_id: str
    ) -> None:
        import json
        await self.db.execute(
            text("""
                UPDATE flux_workflow_runs
                SET context = :ctx::jsonb,
                    current_node_id = :node_id
                WHERE id = :rid
            """),
            {
                "rid": str(run_id),
                "ctx": json.dumps(context),
                "node_id": current_node_id,
            },
        )
        await self.db.commit()

    async def _mark_suspended(
        self, run_id: UUID, node_id: str
    ) -> None:
        await self.db.execute(
            text("""
                UPDATE flux_workflow_runs
                SET status = 'suspended',
                    current_node_id = :node_id
                WHERE id = :rid
            """),
            {"rid": str(run_id), "node_id": node_id},
        )
        await self.db.commit()

    async def _mark_completed(self, run_id: UUID) -> None:
        await self.db.execute(
            text("""
                UPDATE flux_workflow_runs
                SET status = 'completed',
                    completed_at = NOW()
                WHERE id = :rid
            """),
            {"rid": str(run_id)},
        )
        await self.db.commit()

    async def _mark_failed(
        self, run_id: UUID, error: str
    ) -> None:
        await self.db.execute(
            text("""
                UPDATE flux_workflow_runs
                SET status = 'failed',
                    error_message = :error,
                    completed_at = NOW()
                WHERE id = :rid
            """),
            {"rid": str(run_id), "error": error},
        )
        await self.db.commit()
