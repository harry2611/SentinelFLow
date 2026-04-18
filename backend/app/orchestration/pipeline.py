from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from time import perf_counter
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.agents.decision_agent import DecisionAgent
from app.agents.execution_agent import ExecutionAgent
from app.agents.feedback_agent import FeedbackAgent
from app.agents.types import DecisionResult, ExecutionResult, VerificationResult
from app.agents.verifier_agent import VerifierAgent
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.entities import (
    AgentDecision,
    AgentState,
    ExecutionLog,
    FeedbackEvent,
    Task,
    TaskStatus,
    TaskType,
    VerifierResult,
    WorkflowStage,
)
from app.services.memory_service import MemoryService
from app.services.policy_service import PolicyService


@dataclass
class WorkflowContext:
    task: Task
    similar_cases: list[dict[str, Any]] = field(default_factory=list)
    policy_hints: list[str] = field(default_factory=list)
    decision: DecisionResult | None = None
    execution: ExecutionResult | None = None
    verification: VerificationResult | None = None


class WorkflowPipeline:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()
        self.memory_service = MemoryService(db)
        self.policy_service = PolicyService(db)
        self.decision_agent = DecisionAgent()
        self.verifier_agent = VerifierAgent()
        self.feedback_agent = FeedbackAgent(db)

    def run(self, task_id: str, start_stage: str = "decision") -> None:
        task = self.db.scalar(
            select(Task)
            .where(Task.id == UUID(task_id))
            .options(
                selectinload(Task.workflow),
                selectinload(Task.decisions),
                selectinload(Task.verifier_results),
                selectinload(Task.execution_logs),
                selectinload(Task.feedback_events),
            )
        )
        if not task:
            raise ValueError("Task not found")

        context = WorkflowContext(task=task)
        overall_started = perf_counter()
        task.status = TaskStatus.in_progress
        task.workflow.status = TaskStatus.in_progress
        task.workflow.current_stage = (
            WorkflowStage.decision if start_stage == "decision" else WorkflowStage.execution
        )
        task.workflow.started_at = task.workflow.started_at or datetime.now(timezone.utc)
        self._log(task, "System", "pipeline", "Starting workflow execution job.")
        self.db.commit()

        if start_stage == "decision":
            self._run_decision(context)
            if task.status == TaskStatus.awaiting_review:
                self._finalize(task, overall_started)
                return
        else:
            context.decision = self._hydrate_latest_decision(task)

        self._run_execution(context)
        if task.status == TaskStatus.awaiting_review:
            self._finalize(task, overall_started)
            return

        self._run_verification(context)
        self._run_feedback(context)
        self._finalize(task, overall_started)

    def _run_decision(self, context: WorkflowContext) -> None:
        task = context.task
        task.workflow.current_stage = WorkflowStage.decision
        context.similar_cases = self.memory_service.retrieve_similar_cases(
            f"{task.title}\n{task.description}", task.task_type
        )
        context.policy_hints = self.policy_service.get_policy_hints(task.task_type)
        context.decision = self.decision_agent.run(task, context.similar_cases, context.policy_hints)

        decision_record = AgentDecision(
            workflow_id=task.workflow_id,
            task_id=task.id,
            classification=context.decision.classification,
            decision_text=context.decision.decision_text,
            action_plan=context.decision.action_plan,
            recommended_tool=context.decision.recommended_tool,
            confidence=context.decision.confidence,
            rationale=context.decision.rationale,
            similar_cases=context.similar_cases,
            policy_hints=context.policy_hints,
            requires_human_review=context.decision.requires_human_review,
        )
        task.task_type = TaskType(context.decision.classification)
        task.confidence = context.decision.confidence
        task.assignee = context.decision.assignee
        task.decision_summary = context.decision.decision_text
        task.estimated_minutes_saved = context.decision.estimated_minutes_saved
        task.needs_human_review = context.decision.requires_human_review
        task.workflow.shared_context = {
            **task.workflow.shared_context,
            "decision": context.decision.model_dump(mode="json"),
            "similar_cases": context.similar_cases,
            "policy_hints": context.policy_hints,
        }
        self.db.add(decision_record)
        self._snapshot_state(task, "Decision Agent", "decision", task.workflow.shared_context)
        self._log(
            task,
            "Decision Agent",
            "decision",
            context.decision.decision_text,
            {
                "confidence": context.decision.confidence,
                "recommended_tool": context.decision.recommended_tool,
            },
        )
        self.memory_service.store_task_memory(
            task,
            "decision_memory",
            self.memory_service.build_memory_snapshot(task),
            {
                "task_type": context.decision.classification,
                "confidence": context.decision.confidence,
                "status": task.status.value,
            },
        )

        if (
            task.execution_mode.value == "manual"
            or context.decision.requires_human_review
            or context.decision.confidence < self.settings.auto_approval_threshold
        ):
            reason = "Manual mode enabled or confidence below auto-approval threshold."
            self._route_to_review(task, reason)
        self.db.commit()

    def _run_execution(self, context: WorkflowContext) -> None:
        task = context.task
        decision = context.decision or self._hydrate_latest_decision(task)
        if not decision:
            raise ValueError("Missing decision for execution stage")

        task.workflow.current_stage = WorkflowStage.execution
        execution_agent = ExecutionAgent(self.db)
        context.execution = execution_agent.run(task, decision)
        task.resolution_summary = context.execution.summary
        task.workflow.shared_context = {
            **task.workflow.shared_context,
            "execution": context.execution.model_dump(mode="json"),
        }
        self._snapshot_state(
            task, "Execution Agent", "execution", context.execution.model_dump(mode="json")
        )
        self._log(
            task,
            "Execution Agent",
            "execution",
            context.execution.summary,
            {"tool_runs": context.execution.tool_runs},
            latency_ms=context.execution.latency_ms,
        )
        self.db.commit()

    def _run_verification(self, context: WorkflowContext) -> None:
        task = context.task
        decision = context.decision or self._hydrate_latest_decision(task)
        execution = context.execution
        if not decision or not execution:
            raise ValueError("Missing decision or execution data for verification stage")

        task.workflow.current_stage = WorkflowStage.verification
        context.verification = self.verifier_agent.run(task, decision, execution)
        verifier_row = VerifierResult(
            workflow_id=task.workflow_id,
            task_id=task.id,
            passed=context.verification.passed,
            confidence=context.verification.confidence,
            issues=context.verification.issues,
            summary=context.verification.summary,
            recommended_status=context.verification.recommended_status,
        )
        self.db.add(verifier_row)
        task.workflow.shared_context = {
            **task.workflow.shared_context,
            "verification": context.verification.model_dump(mode="json"),
        }
        self._snapshot_state(
            task, "Verifier Agent", "verification", context.verification.model_dump(mode="json")
        )
        self._log(
            task,
            "Verifier Agent",
            "verification",
            context.verification.summary,
            {
                "passed": context.verification.passed,
                "issues": context.verification.issues,
            },
        )

        if (
            not context.verification.passed
            or context.verification.confidence < self.settings.verifier_pass_threshold
        ):
            self._route_to_review(task, "Verifier requested human review before completion.")
        else:
            task.status = TaskStatus.completed
            task.workflow.status = TaskStatus.completed
            task.workflow.current_stage = WorkflowStage.completed
            task.needs_human_review = False
        self.db.commit()

    def _run_feedback(self, context: WorkflowContext) -> None:
        task = context.task
        if not context.decision or not context.execution or not context.verification:
            return
        task.workflow.current_stage = WorkflowStage.feedback
        self.feedback_agent.record_outcome(
            task=task,
            decision=context.decision,
            execution_result=context.execution,
            verification_result=context.verification,
            user_override=task.user_override,
        )
        self.memory_service.store_task_memory(
            task,
            "outcome_memory",
            self.memory_service.build_memory_snapshot(task),
            {
                "task_type": task.task_type.value,
                "status": task.status.value,
                "verifier_passed": context.verification.passed,
            },
        )
        self._snapshot_state(task, "Feedback Agent", "feedback", task.workflow.shared_context)
        self._log(
            task,
            "Feedback Agent",
            "feedback",
            "Outcome and reliability signals recorded for future retrieval.",
        )
        self.db.commit()

    def _finalize(self, task: Task, overall_started: float) -> None:
        task.latency_ms = int((perf_counter() - overall_started) * 1000)
        if task.status == TaskStatus.completed:
            task.workflow.completed_at = datetime.now(timezone.utc)
        self.db.commit()

    def _route_to_review(self, task: Task, reason: str) -> None:
        task.status = TaskStatus.awaiting_review
        task.workflow.status = TaskStatus.awaiting_review
        task.workflow.current_stage = WorkflowStage.review
        task.needs_human_review = True
        self.db.add(
            FeedbackEvent(
                workflow_id=task.workflow_id,
                task_id=task.id,
                event_type="review_required",
                score=0.0,
                notes=reason,
                payload={"reason": reason},
            )
        )
        self._log(task, "System", "review", reason, {"needs_human_review": True})

    def _snapshot_state(
        self, task: Task, agent_name: str, stage: str, state: dict[str, Any]
    ) -> None:
        current_version = (
            self.db.scalar(
                select(func.max(AgentState.version)).where(
                    AgentState.workflow_id == task.workflow_id,
                    AgentState.agent_name == agent_name,
                    AgentState.stage == stage,
                )
            )
            or 0
        )
        self.db.add(
            AgentState(
                workflow_id=task.workflow_id,
                task_id=task.id,
                agent_name=agent_name,
                stage=stage,
                state=state,
                version=current_version + 1,
            )
        )

    def _log(
        self,
        task: Task,
        agent_name: str,
        stage: str,
        message: str,
        payload: dict[str, Any] | None = None,
        latency_ms: int | None = None,
    ) -> None:
        self.db.add(
            ExecutionLog(
                workflow_id=task.workflow_id,
                task_id=task.id,
                agent_name=agent_name,
                stage=stage,
                message=message,
                payload=payload or {},
                latency_ms=latency_ms,
            )
        )

    def _hydrate_latest_decision(self, task: Task) -> DecisionResult | None:
        latest = self.db.scalar(
            select(AgentDecision)
            .where(AgentDecision.task_id == task.id)
            .order_by(AgentDecision.created_at.desc())
            .limit(1)
        )
        if not latest:
            return None
        return DecisionResult(
            classification=latest.classification,
            decision_text=latest.decision_text,
            action_plan=latest.action_plan,
            recommended_tool=latest.recommended_tool,
            confidence=latest.confidence,
            rationale=latest.rationale,
            assignee=task.assignee or "Operations Desk",
            estimated_minutes_saved=task.estimated_minutes_saved,
            requires_human_review=latest.requires_human_review,
            labels=latest.action_plan.get("labels", []),
        )


def process_task_job(task_id: str, start_stage: str = "decision") -> None:
    with SessionLocal() as db:
        try:
            pipeline = WorkflowPipeline(db)
            pipeline.run(task_id, start_stage)
        except Exception as exc:
            task = db.scalar(select(Task).where(Task.id == UUID(task_id)).options(selectinload(Task.workflow)))
            if task and task.workflow:
                task.status = TaskStatus.failed
                task.workflow.status = TaskStatus.failed
                task.workflow.current_stage = WorkflowStage.review
                db.add(
                    ExecutionLog(
                        workflow_id=task.workflow_id,
                        task_id=task.id,
                        agent_name="System",
                        stage="error",
                        level="error",
                        message="Workflow execution failed unexpectedly.",
                        payload={"error": str(exc)},
                    )
                )
                db.commit()
            raise
