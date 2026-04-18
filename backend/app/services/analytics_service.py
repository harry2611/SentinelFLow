from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.entities import AgentDecision, ExecutionLog, Task, TaskStatus, VerifierResult


class AnalyticsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_overview(self) -> dict[str, Any]:
        tasks = self.db.scalars(
            select(Task).options(
                selectinload(Task.decisions),
                selectinload(Task.verifier_results),
                selectinload(Task.execution_logs),
            )
        ).all()
        decisions = self.db.scalars(
            select(AgentDecision).order_by(AgentDecision.created_at.desc()).limit(10)
        ).all()
        verifier_results = self.db.scalars(select(VerifierResult)).all()
        logs = self.db.scalars(
            select(ExecutionLog).order_by(ExecutionLog.created_at.desc()).limit(30)
        ).all()

        status_counts = Counter(task.status.value for task in tasks)
        type_counts = Counter(task.task_type.value for task in tasks)
        total_time_saved = sum(task.estimated_minutes_saved for task in tasks)
        avg_latency = (
            sum(task.latency_ms or 0 for task in tasks) / max(len(tasks), 1)
            if tasks
            else 0
        )
        completed = sum(1 for task in tasks if task.status == TaskStatus.completed)
        auto_resolved = sum(
            1
            for task in tasks
            if task.status == TaskStatus.completed and not task.needs_human_review
        )
        verification_failures = sum(1 for result in verifier_results if not result.passed)
        review_queue = sum(1 for task in tasks if task.status == TaskStatus.awaiting_review)

        trend_map: dict[str, dict[str, int]] = defaultdict(lambda: {"completed": 0, "failed": 0})
        for task in tasks:
            key = task.created_at.date().isoformat()
            if task.status == TaskStatus.completed:
                trend_map[key]["completed"] += 1
            if task.status in {TaskStatus.failed, TaskStatus.rejected}:
                trend_map[key]["failed"] += 1

        memory_examples = []
        for decision in decisions:
            if decision.similar_cases:
                memory_examples.append(
                    {
                        "task_id": str(decision.task_id),
                        "classification": decision.classification,
                        "decision_text": decision.decision_text,
                        "retrieved_cases": decision.similar_cases[:2],
                    }
                )
            if len(memory_examples) >= 3:
                break

        return {
            "headline_metrics": {
                "total_workflows_processed": len(tasks),
                "completed_workflows": completed,
                "auto_resolved_workflows": auto_resolved,
                "verification_failures": verification_failures,
                "review_queue_count": review_queue,
                "time_saved_minutes": total_time_saved,
                "average_latency_ms": round(avg_latency, 2),
                "manual_effort_reduced_pct": round((auto_resolved / max(len(tasks), 1)) * 100, 1),
            },
            "status_counts": dict(status_counts),
            "type_counts": dict(type_counts),
            "resolution_trends": [
                {"date": date_key, **values}
                for date_key, values in sorted(trend_map.items(), key=lambda item: item[0])
            ],
            "recent_decisions": [
                {
                    "task_id": str(decision.task_id),
                    "classification": decision.classification,
                    "confidence": decision.confidence,
                    "tool": decision.recommended_tool,
                    "summary": decision.decision_text,
                    "created_at": decision.created_at.isoformat(),
                }
                for decision in decisions
            ],
            "recent_traces": [
                {
                    "task_id": str(log.task_id),
                    "agent_name": log.agent_name,
                    "stage": log.stage,
                    "message": log.message,
                    "created_at": log.created_at.isoformat(),
                }
                for log in logs
            ],
            "memory_retrieval_examples": memory_examples,
        }

