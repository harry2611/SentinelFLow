from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.entities import (
    ExecutionLog,
    FeedbackEvent,
    Task,
    TaskStatus,
    User,
    Workflow,
    WorkflowStage,
)
from app.schemas.task import ReviewAction, TaskCreate
from app.services.queue_service import enqueue_task


class TaskService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_task(self, payload: TaskCreate) -> tuple[Task, dict[str, Any]]:
        requester = self.db.scalar(select(User).where(User.email == payload.requester_email))
        if not requester:
            requester = User(
                name=payload.requester_name,
                email=payload.requester_email,
                role="Requester",
                team=payload.department,
                is_operator=False,
            )
            self.db.add(requester)
            self.db.flush()

        workflow = Workflow(
            name=f"{payload.task_type.value.replace('_', ' ').title()} Workflow",
            workflow_key=f"{payload.task_type.value}-flow",
            status=TaskStatus.queued,
            current_stage=WorkflowStage.ingestion,
            shared_context={"source": payload.source},
            started_at=None,
            completed_at=None,
        )
        self.db.add(workflow)
        self.db.flush()

        task = Task(
            workflow_id=workflow.id,
            requester_id=requester.id,
            title=payload.title,
            description=payload.description,
            task_type=payload.task_type,
            priority=payload.priority,
            status=TaskStatus.queued,
            execution_mode=payload.execution_mode,
            source=payload.source,
            requester_name=payload.requester_name,
            requester_email=payload.requester_email,
            department=payload.department,
            task_metadata=payload.task_metadata,
        )
        self.db.add(task)
        self.db.flush()
        self.db.add(
            ExecutionLog(
                workflow_id=workflow.id,
                task_id=task.id,
                agent_name="System",
                stage="ingestion",
                message="Task ingested and queued for workflow orchestration.",
                payload={"source": payload.source},
            )
        )
        self.db.commit()

        queue_info = {"queued": False, "job_id": None}
        if payload.auto_process:
            queue_info = enqueue_task(str(task.id))
        task = self.get_task(task.id)
        return task, queue_info

    def list_tasks(
        self,
        status: str | None = None,
        task_type: str | None = None,
        search: str | None = None,
    ) -> list[Task]:
        statement = select(Task).options(selectinload(Task.workflow)).order_by(Task.created_at.desc())
        if status:
            statement = statement.where(Task.status == status)
        if task_type:
            statement = statement.where(Task.task_type == task_type)
        if search:
            like = f"%{search.strip()}%"
            statement = statement.where(
                or_(Task.title.ilike(like), Task.description.ilike(like), Task.requester_name.ilike(like))
            )
        return self.db.scalars(statement).all()

    def get_task(self, task_id: UUID) -> Task:
        task = self.db.scalar(
            select(Task)
            .where(Task.id == task_id)
            .options(
                selectinload(Task.workflow),
                selectinload(Task.requester),
                selectinload(Task.decisions),
                selectinload(Task.execution_logs),
                selectinload(Task.verifier_results),
                selectinload(Task.feedback_events),
                selectinload(Task.states),
            )
        )
        if not task:
            raise ValueError("Task not found")
        task.decisions.sort(key=lambda row: row.created_at, reverse=True)
        task.execution_logs.sort(key=lambda row: row.created_at)
        task.verifier_results.sort(key=lambda row: row.created_at, reverse=True)
        task.feedback_events.sort(key=lambda row: row.created_at, reverse=True)
        task.states.sort(key=lambda row: row.created_at)
        return task

    def get_review_queue(self) -> list[Task]:
        statement = (
            select(Task)
            .where(Task.status == TaskStatus.awaiting_review)
            .options(selectinload(Task.workflow))
            .order_by(Task.updated_at.desc())
        )
        return self.db.scalars(statement).all()

    def approve_task(self, task_id: UUID, action: ReviewAction) -> tuple[Task, dict[str, Any]]:
        task = self.get_task(task_id)
        task.user_override = True
        task.needs_human_review = False
        self.db.add(
            FeedbackEvent(
                workflow_id=task.workflow_id,
                task_id=task.id,
                event_type="human_approved",
                score=1.0,
                notes=action.notes or f"Approved by {action.reviewer_name}.",
                payload={"reviewer_name": action.reviewer_name},
            )
        )
        self.db.add(
            ExecutionLog(
                workflow_id=task.workflow_id,
                task_id=task.id,
                agent_name="Human Review",
                stage="review",
                message=action.notes or "Task approved for completion or resumed automation.",
                payload={"reviewer_name": action.reviewer_name},
            )
        )

        if action.override_complete or task.verifier_results:
            task.status = TaskStatus.completed
            task.workflow.status = TaskStatus.completed
            task.workflow.current_stage = WorkflowStage.completed
            task.workflow.completed_at = datetime.now(timezone.utc)
            task.resolution_summary = (
                task.resolution_summary or "Completed after human-in-the-loop approval."
            )
            self.db.commit()
            return self.get_task(task.id), {"queued": False, "job_id": None}

        task.status = TaskStatus.queued
        task.workflow.status = TaskStatus.queued
        task.workflow.current_stage = WorkflowStage.execution
        self.db.commit()
        queue_info = enqueue_task(str(task.id), start_stage="execution")
        return self.get_task(task.id), queue_info

    def reject_task(self, task_id: UUID, action: ReviewAction) -> Task:
        task = self.get_task(task_id)
        task.status = TaskStatus.rejected
        task.workflow.status = TaskStatus.rejected
        task.workflow.current_stage = WorkflowStage.review
        task.needs_human_review = False
        task.user_override = True
        self.db.add(
            FeedbackEvent(
                workflow_id=task.workflow_id,
                task_id=task.id,
                event_type="human_rejected",
                score=0.0,
                notes=action.notes or f"Rejected by {action.reviewer_name}.",
                payload={"reviewer_name": action.reviewer_name},
            )
        )
        self.db.add(
            ExecutionLog(
                workflow_id=task.workflow_id,
                task_id=task.id,
                agent_name="Human Review",
                stage="review",
                message=action.notes or "Task rejected by operator.",
                payload={"reviewer_name": action.reviewer_name},
            )
        )
        self.db.commit()
        return self.get_task(task.id)
