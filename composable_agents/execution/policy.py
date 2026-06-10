"""Tunable execution policy shared by all execution backends (a §6 open seam).

Pure dataclass + JSON codec; no engine imports, so the Temporal harness and the
DBOS backend both consume it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class ExecutionPolicy:
    hand_timeout_s: int = 30
    brain_timeout_s: int = 120
    plan_timeout_s: int = 120
    sub_task_timeout_s: int = 3600
    agent_task_timeout_s: int = 3600
    # Retry shaping.
    idempotent_max_attempts: int = 5
    write_max_attempts: int = 3
    initial_retry_s: float = 1.0
    retry_backoff: float = 2.0
    max_retry_interval_s: int = 60
    trace_content_refs: bool = False
    max_parallel: Optional[int] = None

    def to_json(self) -> dict[str, Any]:
        out = {
            "handTimeoutS": self.hand_timeout_s,
            "brainTimeoutS": self.brain_timeout_s,
            "planTimeoutS": self.plan_timeout_s,
            "subTaskTimeoutS": self.sub_task_timeout_s,
            "agentTaskTimeoutS": self.agent_task_timeout_s,
            "idempotentMaxAttempts": self.idempotent_max_attempts,
            "writeMaxAttempts": self.write_max_attempts,
            "initialRetryS": self.initial_retry_s,
            "retryBackoff": self.retry_backoff,
            "maxRetryIntervalS": self.max_retry_interval_s,
            "traceContentRefs": self.trace_content_refs,
        }
        if self.max_parallel is not None:
            out["maxParallel"] = self.max_parallel
        return out

    @staticmethod
    def from_json(d: Optional[dict[str, Any]]) -> "ExecutionPolicy":
        d = d or {}
        base = ExecutionPolicy()
        return ExecutionPolicy(
            hand_timeout_s=d.get("handTimeoutS", base.hand_timeout_s),
            brain_timeout_s=d.get("brainTimeoutS", base.brain_timeout_s),
            plan_timeout_s=d.get("planTimeoutS", base.plan_timeout_s),
            sub_task_timeout_s=d.get("subTaskTimeoutS", base.sub_task_timeout_s),
            agent_task_timeout_s=d.get("agentTaskTimeoutS", base.agent_task_timeout_s),
            idempotent_max_attempts=d.get("idempotentMaxAttempts", base.idempotent_max_attempts),
            write_max_attempts=d.get("writeMaxAttempts", base.write_max_attempts),
            initial_retry_s=d.get("initialRetryS", base.initial_retry_s),
            retry_backoff=d.get("retryBackoff", base.retry_backoff),
            max_retry_interval_s=d.get("maxRetryIntervalS", base.max_retry_interval_s),
            trace_content_refs=d.get("traceContentRefs", base.trace_content_refs),
            max_parallel=d.get("maxParallel", base.max_parallel),
        )
