from __future__ import annotations

from collections import Counter

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.entities import FeedbackEvent, Task, TaskStatus, TaskType


class PolicyService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_policy_hints(self, task_type: TaskType) -> list[str]:
        hints: list[str] = []
        recent_tasks = self.db.scalars(
            select(Task)
            .where(Task.task_type == task_type)
            .order_by(desc(Task.updated_at))
            .limit(8)
        ).all()
        successful = [task for task in recent_tasks if task.status == TaskStatus.completed]
        flagged = [task for task in recent_tasks if task.needs_human_review]

        if successful:
            assignee_counts = Counter(task.assignee for task in successful if task.assignee)
            if assignee_counts:
                top_assignee, _ = assignee_counts.most_common(1)[0]
                hints.append(f"Successful runs in this workflow were commonly owned by {top_assignee}.")
            avg_saved = sum(task.estimated_minutes_saved for task in successful) / len(successful)
            hints.append(f"Similar successful workflows saved about {avg_saved:.0f} minutes on average.")
        if flagged:
            hints.append("Recent flagged runs suggest using human review when scope or requester intent is ambiguous.")

        recent_feedback = self.db.scalars(
            select(FeedbackEvent)
            .join(Task, FeedbackEvent.task_id == Task.id)
            .where(Task.task_type == task_type)
            .order_by(desc(FeedbackEvent.created_at))
            .limit(5)
        ).all()
        for event in recent_feedback:
            if event.notes:
                hints.append(event.notes)
        return hints[:4]

