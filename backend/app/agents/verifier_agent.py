from __future__ import annotations

from app.agents.types import DecisionResult, ExecutionResult, VerificationResult
from app.models.entities import Task
from app.services.llm_service import LLMService


class VerifierAgent:
    name = "Verifier Agent"

    def __init__(self) -> None:
        self.llm_service = LLMService()

    def run(
        self, task: Task, decision: DecisionResult, execution_result: ExecutionResult
    ) -> VerificationResult:
        return self.llm_service.verify_execution(
            task=task,
            decision=decision,
            execution_summary=execution_result.model_dump(),
        )

