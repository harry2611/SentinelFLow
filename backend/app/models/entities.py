import enum
import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class TaskType(str, enum.Enum):
    support = "support"
    onboarding = "onboarding"
    internal_ops = "internal_ops"
    follow_up = "follow_up"


class TaskStatus(str, enum.Enum):
    queued = "queued"
    in_progress = "in_progress"
    awaiting_review = "awaiting_review"
    completed = "completed"
    failed = "failed"
    rejected = "rejected"


class WorkflowStage(str, enum.Enum):
    ingestion = "ingestion"
    decision = "decision"
    execution = "execution"
    verification = "verification"
    review = "review"
    feedback = "feedback"
    completed = "completed"


class ExecutionMode(str, enum.Enum):
    manual = "manual"
    semi_autonomous = "semi_autonomous"
    autonomous = "autonomous"


class TaskPriority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"


class IntegrationType(str, enum.Enum):
    zapier = "zapier"
    email = "email"
    internal_api = "internal_api"
    webhook = "webhook"


class IntegrationStatus(str, enum.Enum):
    healthy = "healthy"
    degraded = "degraded"
    offline = "offline"


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    role: Mapped[str] = mapped_column(String(80), nullable=False)
    team: Mapped[str] = mapped_column(String(120), nullable=False)
    is_operator: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    tasks_requested: Mapped[list["Task"]] = relationship(
        back_populates="requester", foreign_keys="Task.requester_id"
    )


class Workflow(TimestampMixin, Base):
    __tablename__ = "workflows"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    workflow_key: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, name="task_status"), default=TaskStatus.queued, nullable=False
    )
    current_stage: Mapped[WorkflowStage] = mapped_column(
        Enum(WorkflowStage, name="workflow_stage"),
        default=WorkflowStage.ingestion,
        nullable=False,
    )
    shared_context: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    task: Mapped["Task"] = relationship(back_populates="workflow", uselist=False)
    decisions: Mapped[list["AgentDecision"]] = relationship(back_populates="workflow")
    execution_logs: Mapped[list["ExecutionLog"]] = relationship(back_populates="workflow")
    verifier_results: Mapped[list["VerifierResult"]] = relationship(
        back_populates="workflow"
    )
    feedback_events: Mapped[list["FeedbackEvent"]] = relationship(
        back_populates="workflow"
    )
    states: Mapped[list["AgentState"]] = relationship(back_populates="workflow")
    memories: Mapped[list["MemoryEmbedding"]] = relationship(back_populates="workflow")

    @property
    def agent_states(self) -> list["AgentState"]:
        return self.states


class Task(TimestampMixin, Base):
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    workflow_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workflows.id"), nullable=False, unique=True
    )
    requester_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    title: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    task_type: Mapped[TaskType] = mapped_column(
        Enum(TaskType, name="task_type"), default=TaskType.internal_ops, nullable=False
    )
    priority: Mapped[TaskPriority] = mapped_column(
        Enum(TaskPriority, name="task_priority"),
        default=TaskPriority.medium,
        nullable=False,
    )
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, name="task_status"), default=TaskStatus.queued, nullable=False
    )
    execution_mode: Mapped[ExecutionMode] = mapped_column(
        Enum(ExecutionMode, name="execution_mode"),
        default=ExecutionMode.semi_autonomous,
        nullable=False,
    )
    source: Mapped[str] = mapped_column(String(80), default="dashboard", nullable=False)
    requester_name: Mapped[str] = mapped_column(String(120), nullable=False)
    requester_email: Mapped[str] = mapped_column(String(255), nullable=False)
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float)
    assignee: Mapped[str | None] = mapped_column(String(120))
    decision_summary: Mapped[str | None] = mapped_column(Text)
    resolution_summary: Mapped[str | None] = mapped_column(Text)
    estimated_minutes_saved: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    needs_human_review: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    user_override: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    task_metadata: Mapped[dict] = mapped_column("metadata", JSON, default=dict, nullable=False)

    workflow: Mapped["Workflow"] = relationship(back_populates="task")
    requester: Mapped[User | None] = relationship(back_populates="tasks_requested")
    decisions: Mapped[list["AgentDecision"]] = relationship(back_populates="task")
    execution_logs: Mapped[list["ExecutionLog"]] = relationship(back_populates="task")
    verifier_results: Mapped[list["VerifierResult"]] = relationship(back_populates="task")
    feedback_events: Mapped[list["FeedbackEvent"]] = relationship(back_populates="task")
    states: Mapped[list["AgentState"]] = relationship(back_populates="task")
    memories: Mapped[list["MemoryEmbedding"]] = relationship(back_populates="task")

    @property
    def agent_states(self) -> list["AgentState"]:
        return self.states


class AgentDecision(Base):
    __tablename__ = "agent_decisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workflow_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workflows.id"), nullable=False
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False
    )
    classification: Mapped[str] = mapped_column(String(80), nullable=False)
    decision_text: Mapped[str] = mapped_column(Text, nullable=False)
    action_plan: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    recommended_tool: Mapped[str] = mapped_column(String(120), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    similar_cases: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    policy_hints: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    requires_human_review: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    workflow: Mapped[Workflow] = relationship(back_populates="decisions")
    task: Mapped[Task] = relationship(back_populates="decisions")


class ExecutionLog(Base):
    __tablename__ = "execution_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workflow_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workflows.id"), nullable=False, index=True
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False, index=True
    )
    agent_name: Mapped[str] = mapped_column(String(120), nullable=False)
    stage: Mapped[str] = mapped_column(String(80), nullable=False)
    level: Mapped[str] = mapped_column(String(20), default="info", nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    workflow: Mapped[Workflow] = relationship(back_populates="execution_logs")
    task: Mapped[Task] = relationship(back_populates="execution_logs")


class VerifierResult(Base):
    __tablename__ = "verifier_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workflow_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workflows.id"), nullable=False
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False
    )
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    issues: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_status: Mapped[str] = mapped_column(String(40), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    workflow: Mapped[Workflow] = relationship(back_populates="verifier_results")
    task: Mapped[Task] = relationship(back_populates="verifier_results")


class FeedbackEvent(Base):
    __tablename__ = "feedback_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workflow_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workflows.id"), nullable=False
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    score: Mapped[float | None] = mapped_column(Float)
    notes: Mapped[str | None] = mapped_column(Text)
    payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    workflow: Mapped[Workflow] = relationship(back_populates="feedback_events")
    task: Mapped[Task] = relationship(back_populates="feedback_events")


class AgentState(Base):
    __tablename__ = "agent_states"
    __table_args__ = (
        UniqueConstraint("workflow_id", "agent_name", "stage", "version", name="uq_state"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workflow_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workflows.id"), nullable=False
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False
    )
    agent_name: Mapped[str] = mapped_column(String(120), nullable=False)
    stage: Mapped[str] = mapped_column(String(80), nullable=False)
    state: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    workflow: Mapped[Workflow] = relationship(back_populates="states")
    task: Mapped[Task] = relationship(back_populates="states")


class Integration(TimestampMixin, Base):
    __tablename__ = "integrations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False, unique=True)
    integration_type: Mapped[IntegrationType] = mapped_column(
        Enum(IntegrationType, name="integration_type"), nullable=False
    )
    status: Mapped[IntegrationStatus] = mapped_column(
        Enum(IntegrationStatus, name="integration_status"),
        default=IntegrationStatus.healthy,
        nullable=False,
    )
    endpoint: Mapped[str | None] = mapped_column(String(500))
    auth_type: Mapped[str | None] = mapped_column(String(80))
    secret_hint: Mapped[str | None] = mapped_column(String(120))
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    config: Mapped[dict] = mapped_column("metadata", JSON, default=dict, nullable=False)
    last_ping_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class MemoryEmbedding(Base):
    __tablename__ = "memory_embeddings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workflow_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workflows.id")
    )
    task_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("tasks.id"))
    memory_type: Mapped[str] = mapped_column(String(80), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(1536), nullable=False)
    memory_metadata: Mapped[dict] = mapped_column("metadata", JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    workflow: Mapped[Workflow | None] = relationship(back_populates="memories")
    task: Mapped[Task | None] = relationship(back_populates="memories")
