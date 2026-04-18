from typing import Any

from pydantic import BaseModel, Field


class DecisionResult(BaseModel):
    classification: str
    decision_text: str
    action_plan: dict[str, Any]
    recommended_tool: str
    confidence: float
    rationale: str
    assignee: str
    estimated_minutes_saved: int = 0
    requires_human_review: bool = False
    labels: list[str] = Field(default_factory=list)


class ExecutionResult(BaseModel):
    success: bool
    summary: str
    tool_runs: list[dict[str, Any]] = Field(default_factory=list)
    output: dict[str, Any] = Field(default_factory=dict)
    latency_ms: int = 0
    escalation_reason: str | None = None


class VerificationResult(BaseModel):
    passed: bool
    confidence: float
    issues: list[str] = Field(default_factory=list)
    summary: str
    recommended_status: str

