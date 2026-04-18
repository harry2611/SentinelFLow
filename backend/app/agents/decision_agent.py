from __future__ import annotations

from app.agents.types import DecisionResult
from app.models.entities import Task
from app.services.llm_service import LLMService


class DecisionAgent:
    name = "Decision Agent"

    def __init__(self) -> None:
        self.llm_service = LLMService()

    def run(self, task: Task, similar_cases: list[dict], policy_hints: list[str]) -> DecisionResult:
        return self.llm_service.generate_decision(task, similar_cases, policy_hints)

