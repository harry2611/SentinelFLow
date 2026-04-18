from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.entities import (
    ExecutionMode,
    TaskPriority,
    TaskStatus,
    TaskType,
    WorkflowStage,
)
from app.schemas.common import TaskSummary, UserSummary, WorkflowSummary


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=180)
    description: str = Field(..., min_length=20)
    requester_name: str
    requester_email: EmailStr
    department: str
    task_type: TaskType = TaskType.internal_ops
    priority: TaskPriority = TaskPriority.medium
    execution_mode: ExecutionMode = ExecutionMode.semi_autonomous
    source: str = "dashboard"
    task_metadata: dict[str, Any] = Field(default_factory=dict)
    auto_process: bool = True


class ReviewAction(BaseModel):
    reviewer_name: str = "Human Operator"
    notes: str | None = None
    override_complete: bool = False


class AgentDecisionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    classification: str
    decision_text: str
    action_plan: dict[str, Any]
    recommended_tool: str
    confidence: float
    rationale: str
    similar_cases: list[Any]
    policy_hints: list[Any]
    requires_human_review: bool
    created_at: datetime


class ExecutionLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    agent_name: str
    stage: str
    level: str
    message: str
    payload: dict[str, Any]
    latency_ms: int | None = None
    created_at: datetime


class VerifierResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    passed: bool
    confidence: float
    issues: list[Any]
    summary: str
    recommended_status: str
    created_at: datetime


class FeedbackEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_type: str
    score: float | None = None
    notes: str | None = None
    payload: dict[str, Any]
    created_at: datetime


class AgentStateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    agent_name: str
    stage: str
    state: dict[str, Any]
    version: int
    created_at: datetime


class TaskDetailResponse(TaskSummary):
    workflow: WorkflowSummary
    requester: UserSummary | None = None
    decisions: list[AgentDecisionResponse]
    execution_logs: list[ExecutionLogResponse]
    verifier_results: list[VerifierResultResponse]
    feedback_events: list[FeedbackEventResponse]
    agent_states: list[AgentStateResponse]


class WorkflowDetailResponse(WorkflowSummary):
    task_id: UUID
    execution_logs: list[ExecutionLogResponse]
    agent_states: list[AgentStateResponse]


class TaskCreateResponse(BaseModel):
    task: TaskDetailResponse
    queue: dict[str, Any]

