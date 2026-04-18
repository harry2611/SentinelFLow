from __future__ import annotations

from sqlalchemy.orm import Session

from app.agents.types import DecisionResult, ExecutionResult, VerificationResult
from app.models.entities import FeedbackEvent, Task


class FeedbackAgent:
    name = "Feedback Agent"

    def __init__(self, db: Session) -> None:
        self.db = db

    def record_outcome(
        self,
        task: Task,
        decision: DecisionResult,
        execution_result: ExecutionResult,
        verification_result: VerificationResult,
        user_override: bool = False,
    ) -> None:
        feedback_events = [
            FeedbackEvent(
                workflow_id=task.workflow_id,
                task_id=task.id,
                event_type="execution_success",
                score=1.0 if execution_result.success else 0.0,
                notes="Execution outcome captured for policy refinement.",
                payload={
                    "latency_ms": execution_result.latency_ms,
                    "tool_runs": execution_result.tool_runs,
                },
            ),
            FeedbackEvent(
                workflow_id=task.workflow_id,
                task_id=task.id,
                event_type="verifier_result",
                score=verification_result.confidence,
                notes="Verifier reviewed the execution output.",
                payload={
                    "passed": verification_result.passed,
                    "issues": verification_result.issues,
                },
            ),
            FeedbackEvent(
                workflow_id=task.workflow_id,
                task_id=task.id,
                event_type="user_override",
                score=1.0 if user_override else 0.0,
                notes="Human override signal for future routing decisions.",
                payload={"user_override": user_override},
            ),
            FeedbackEvent(
                workflow_id=task.workflow_id,
                task_id=task.id,
                event_type="reliability_score",
                score=round((decision.confidence + verification_result.confidence) / 2, 2),
                notes="Blended reliability signal.",
                payload={"decision_confidence": decision.confidence},
            ),
        ]
        for event in feedback_events:
            self.db.add(event)

