from __future__ import annotations

from typing import Any

from app.models.entities import ExecutionMode, TaskType
from app.schemas.task import TaskCreate
from app.services.task_service import TaskService


DEMO_TEMPLATES: dict[TaskType, dict[str, Any]] = {
    TaskType.support: {
        "title": "Escalate billing export failure for enterprise account",
        "description": (
            "Acme's finance lead reports that scheduled billing exports have failed for two days. "
            "Route the case, notify the requester, and emit an external incident update."
        ),
        "department": "Support",
        "requester_name": "Priya Shah",
        "requester_email": "priya.shah@example.com",
        "priority": "high",
        "task_metadata": {"notify_external": True},
    },
    TaskType.onboarding: {
        "title": "Prepare onboarding plan for new RevOps analyst",
        "description": (
            "A new RevOps analyst starts Monday. Create the checklist, provision core SaaS access, "
            "and notify the hiring manager with readiness status."
        ),
        "department": "People Ops",
        "requester_name": "Melanie Ortiz",
        "requester_email": "melanie.ortiz@example.com",
        "priority": "medium",
        "task_metadata": {"manager_email": "manager@example.com", "access_bundle": "revops-stack"},
    },
    TaskType.internal_ops: {
        "title": "Assign procurement owner for urgent contractor laptop request",
        "description": (
            "A contractor starts in 48 hours and needs a laptop order plus Slack, Notion, and Jira "
            "provisioning. Route to the correct ops owner and open the supporting ticket."
        ),
        "department": "Operations",
        "requester_name": "Noah Lee",
        "requester_email": "noah.lee@example.com",
        "priority": "urgent",
        "task_metadata": {"notify_external": False},
    },
    TaskType.follow_up: {
        "title": "Follow up on unresolved invoice sync incident",
        "description": (
            "A customer success manager needs an automated follow-up sequence for an unresolved invoice "
            "sync issue that is approaching SLA breach."
        ),
        "department": "Customer Success",
        "requester_name": "Angela Brooks",
        "requester_email": "angela.brooks@example.com",
        "priority": "high",
        "task_metadata": {"recipient_email": "client-ops@example.com", "days_until_due": 1},
    },
}


class DemoService:
    def __init__(self, task_service: TaskService) -> None:
        self.task_service = task_service

    def run(self, template: TaskType | None, execution_mode: ExecutionMode) -> list[dict[str, Any]]:
        templates = [template] if template else list(DEMO_TEMPLATES.keys())
        results = []
        for template_key in templates:
            definition = DEMO_TEMPLATES[template_key]
            task, queue = self.task_service.create_task(
                TaskCreate(
                    title=definition["title"],
                    description=definition["description"],
                    requester_name=definition["requester_name"],
                    requester_email=definition["requester_email"],
                    department=definition["department"],
                    task_type=template_key,
                    priority=definition["priority"],
                    execution_mode=execution_mode,
                    source="demo",
                    task_metadata=definition["task_metadata"],
                    auto_process=True,
                )
            )
            results.append({"task_id": str(task.id), "title": task.title, "queue": queue})
        return results

