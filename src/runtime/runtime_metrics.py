import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class RuntimeMetrics:
    """
    Capa de gobernanza de métricas del runtime para dashboards empresariales (Sprint D.2E)
    """
    def __init__(self, event_bus=None):
        self.event_bus = event_bus
        self.metrics = {
            "debate_success_rate": 0.0,
            "tool_failures": 0,
            "human_handoff_rate": 0.0,
            "approval_latency_ms": 0,
            "graph_recovery_count": 0,
            "replay_count": 0,
            "token_consumption": 0,
            "average_turns": 0.0,
        }
        self._counters = {
            "total_debates": 0,
            "successful_debates": 0,
            "total_human_handoffs": 0,
            "total_flows": 0,
            "total_turns": 0,
            "total_approval_latency": 0,
            "total_approvals": 0
        }

    def record_debate(self, success: bool):
        self._counters["total_debates"] += 1
        if success:
            self._counters["successful_debates"] += 1
        self.metrics["debate_success_rate"] = self._counters["successful_debates"] / self._counters["total_debates"]

    def record_tool_failure(self):
        self.metrics["tool_failures"] += 1

    def record_handoff(self):
        self._counters["total_human_handoffs"] += 1
        self._update_handoff_rate()

    def record_flow_completion(self, turns: int):
        self._counters["total_flows"] += 1
        self._counters["total_turns"] += turns
        self.metrics["average_turns"] = self._counters["total_turns"] / self._counters["total_flows"]
        self._update_handoff_rate()

    def _update_handoff_rate(self):
        if self._counters["total_flows"] > 0:
            self.metrics["human_handoff_rate"] = self._counters["total_human_handoffs"] / self._counters["total_flows"]

    def record_approval(self, latency_ms: int):
        self._counters["total_approvals"] += 1
        self._counters["total_approval_latency"] += latency_ms
        self.metrics["approval_latency_ms"] = self._counters["total_approval_latency"] // self._counters["total_approvals"]

    def record_recovery(self):
        self.metrics["graph_recovery_count"] += 1

    def record_replay(self):
        self.metrics["replay_count"] += 1

    def record_tokens(self, tokens: int):
        self.metrics["token_consumption"] += tokens
        
    async def publish_metrics(self):
        if self.event_bus:
            # TODO: Publish EVENT_RUNTIME_METRICS_UPDATED
            pass
