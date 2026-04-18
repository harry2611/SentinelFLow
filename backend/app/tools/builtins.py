from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.models.entities import Integration, IntegrationStatus, Task
from app.tools.base import AgentTool


class InternalApiTool(AgentTool):
    name = "internal_api"

    def execute(
        self,
        db: Session,
        task: Task,
        step: dict[str, Any],
        integrations: dict[str, Integration],
    ) -> dict[str, Any]:
        operation = step.get("operation")
        payload = {
            "success": True,
            "operation": operation,
            "ticket_reference": f"OPS-{str(task.id)[:8].upper()}",
            "details": step,
        }
        if operation == "create_support_case":
            payload["queue"] = step.get("queue", "support-general")
        if operation == "provision_access_bundle":
            payload["bundle"] = step.get("bundle", "core-saas")
        return payload


class EmailSimulationTool(AgentTool):
    name = "email"

    def execute(
        self,
        db: Session,
        task: Task,
        step: dict[str, Any],
        integrations: dict[str, Integration],
    ) -> dict[str, Any]:
        recipient = step.get("recipient", task.requester_email)
        return {
            "success": True,
            "operation": step.get("operation"),
            "recipient": recipient,
            "subject": f"[SentinelFlow] {task.title}",
            "preview": f"Automated workflow update sent to {recipient}.",
        }


class TaskManagerTool(AgentTool):
    name = "task_manager"

    def execute(
        self,
        db: Session,
        task: Task,
        step: dict[str, Any],
        integrations: dict[str, Integration],
    ) -> dict[str, Any]:
        operation = step.get("operation")
        if operation == "create_checklist":
            return {
                "success": True,
                "operation": operation,
                "items_created": step.get("items", []),
            }
        if operation == "schedule_follow_up":
            due_date = datetime.now(timezone.utc) + timedelta(days=step.get("days_until_due", 2))
            return {
                "success": True,
                "operation": operation,
                "follow_up_due_at": due_date.isoformat(),
            }
        return {
            "success": True,
            "operation": operation,
            "owner": step.get("owner", "ops-queue"),
        }


class ZapierWebhookTool(AgentTool):
    name = "zapier"

    def execute(
        self,
        db: Session,
        task: Task,
        step: dict[str, Any],
        integrations: dict[str, Integration],
    ) -> dict[str, Any]:
        integration = integrations.get("zapier")
        if not step.get("enabled", True):
            return {"success": True, "operation": step.get("operation"), "skipped": True}
        if not integration or not integration.endpoint:
            return {
                "success": True,
                "operation": step.get("operation"),
                "mode": "simulated",
                "message": "No Zapier endpoint configured; dry-run event captured.",
            }
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.post(
                    integration.endpoint,
                    json={
                        "task_id": str(task.id),
                        "workflow_id": str(task.workflow_id),
                        "title": task.title,
                        "task_type": task.task_type.value,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                )
            integration.status = (
                IntegrationStatus.healthy if response.status_code < 400 else IntegrationStatus.degraded
            )
            integration.last_ping_at = datetime.now(timezone.utc)
            db.add(integration)
            return {
                "success": response.status_code < 400,
                "operation": step.get("operation"),
                "status_code": response.status_code,
            }
        except Exception as exc:
            integration.status = IntegrationStatus.offline if integration else IntegrationStatus.offline
            if integration:
                integration.last_ping_at = datetime.now(timezone.utc)
                db.add(integration)
            return {"success": False, "operation": step.get("operation"), "error": str(exc)}

