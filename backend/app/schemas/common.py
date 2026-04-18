from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.entities import ExecutionMode, TaskPriority, TaskStatus, TaskType, WorkflowStage


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class UserSummary(BaseSchema):
    id: UUID
    name: str
    email: str
    role: str
    team: str


class WorkflowSummary(BaseSchema):
    id: UUID
    name: str
    workflow_key: str
    status: TaskStatus
    current_stage: WorkflowStage
    shared_context: dict[str, Any]
    started_at: datetime | None = None
    completed_at: datetime | None = None


class TaskSummary(BaseSchema):
    id: UUID
    title: str
    description: str
    task_type: TaskType
    priority: TaskPriority
    status: TaskStatus
    execution_mode: ExecutionMode
    source: str
    requester_name: str
    requester_email: str
    department: str
    confidence: float | None = None
    assignee: str | None = None
    decision_summary: str | None = None
    resolution_summary: str | None = None
    estimated_minutes_saved: int
    latency_ms: int | None = None
    needs_human_review: bool
    user_override: bool
    task_metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime
