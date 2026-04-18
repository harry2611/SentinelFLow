from __future__ import annotations

from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.entities import MemoryEmbedding, Task, TaskStatus, TaskType
from app.services.llm_service import LLMService


class MemoryService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.llm = LLMService()

    def retrieve_similar_cases(
        self, query_text: str, task_type: TaskType | None = None, limit: int = 5
    ) -> list[dict[str, Any]]:
        try:
            query_embedding = self.llm.embed_text(query_text)
            statement = select(MemoryEmbedding).order_by(
                MemoryEmbedding.embedding.cosine_distance(query_embedding)
            ).limit(limit)
            rows = self.db.scalars(statement).all()
            if task_type:
                rows = [
                    row
                    for row in rows
                    if row.memory_metadata.get("task_type") == task_type.value
                ]
            return [
                {
                    "content": row.content,
                    "task_id": str(row.task_id) if row.task_id else None,
                    "workflow_id": str(row.workflow_id) if row.workflow_id else None,
                    "metadata": row.memory_metadata,
                }
                for row in rows
            ]
        except Exception:
            statement = select(MemoryEmbedding).order_by(desc(MemoryEmbedding.created_at)).limit(limit)
            rows = self.db.scalars(statement).all()
            if task_type:
                rows = [
                    row
                    for row in rows
                    if row.memory_metadata.get("task_type") == task_type.value
                ]
            return [
                {
                    "content": row.content,
                    "task_id": str(row.task_id) if row.task_id else None,
                    "workflow_id": str(row.workflow_id) if row.workflow_id else None,
                    "metadata": row.memory_metadata,
                }
                for row in rows
            ]

    def store_task_memory(
        self,
        task: Task,
        memory_type: str,
        content: str,
        metadata: dict[str, Any],
    ) -> None:
        embedding = self.llm.embed_text(content)
        self.db.add(
            MemoryEmbedding(
                workflow_id=task.workflow_id,
                task_id=task.id,
                memory_type=memory_type,
                content=content,
                embedding=embedding,
                memory_metadata=metadata,
            )
        )

    def build_memory_snapshot(self, task: Task) -> str:
        return (
            f"Task: {task.title}\n"
            f"Type: {task.task_type.value}\n"
            f"Priority: {task.priority.value}\n"
            f"Decision: {task.decision_summary or 'pending'}\n"
            f"Outcome: {task.resolution_summary or task.status.value}"
        )

    def successful_patterns(self, task_type: TaskType, limit: int = 5) -> list[Task]:
        statement = (
            select(Task)
            .where(Task.task_type == task_type, Task.status == TaskStatus.completed)
            .order_by(desc(Task.updated_at))
            .limit(limit)
        )
        return self.db.scalars(statement).all()
