from __future__ import annotations

from time import perf_counter

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.types import DecisionResult, ExecutionResult
from app.models.entities import Integration, Task
from app.tools.registry import ToolRegistry


class ExecutionAgent:
    name = "Execution Agent"

    def __init__(self, db: Session) -> None:
        self.db = db
        self.registry = ToolRegistry()

    def run(self, task: Task, decision: DecisionResult) -> ExecutionResult:
        integrations = {
            integration.integration_type.value: integration
            for integration in self.db.scalars(select(Integration)).all()
        }
        tool_runs = []
        overall_success = True
        started = perf_counter()

        for step in decision.action_plan.get("steps", []):
            try:
                tool = self.registry.get(step["tool"])
                result = tool.execute(self.db, task, step, integrations)
            except Exception as exc:
                result = {
                    "success": False,
                    "operation": step.get("operation"),
                    "error": str(exc),
                }
                tool = type("FallbackTool", (), {"name": step.get("tool", "unknown")})()
            tool_runs.append({"tool": tool.name, **result})
            overall_success = overall_success and result.get("success", False)

        latency_ms = int((perf_counter() - started) * 1000)
        summary = (
            f"Executed {len(tool_runs)} tool actions for {decision.classification} workflow."
            if overall_success
            else "Execution completed with degraded results and requires review."
        )
        return ExecutionResult(
            success=overall_success,
            summary=summary,
            tool_runs=tool_runs,
            output={
                "assignee": decision.assignee,
                "labels": decision.labels,
                "recommended_tool": decision.recommended_tool,
            },
            latency_ms=latency_ms,
            escalation_reason=None if overall_success else "tool_failure",
        )
