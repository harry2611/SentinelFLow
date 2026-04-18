from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.entities import (
    AgentDecision,
    AgentState,
    ExecutionLog,
    ExecutionMode,
    FeedbackEvent,
    Integration,
    IntegrationStatus,
    IntegrationType,
    Task,
    TaskPriority,
    TaskStatus,
    TaskType,
    User,
    VerifierResult,
    Workflow,
    WorkflowStage,
)
from app.services.memory_service import MemoryService


def seed_if_empty(session: Session) -> None:
    now = datetime.now(timezone.utc)
    users = [
        User(
            name="Ava Bennett",
            email="ava.bennett@sentinelflow.dev",
            role="Operations Lead",
            team="Operations",
            is_operator=True,
        ),
        User(
            name="Jon Park",
            email="jon.park@sentinelflow.dev",
            role="Support Manager",
            team="Support",
            is_operator=True,
        ),
        User(
            name="Mina Flores",
            email="mina.flores@sentinelflow.dev",
            role="People Ops Partner",
            team="People",
            is_operator=True,
        ),
    ]
    session.add_all(users)
    session.flush()

    integrations = [
        Integration(
            name="Zapier Production Webhook",
            integration_type=IntegrationType.zapier,
            status=IntegrationStatus.healthy,
            endpoint=None,
            auth_type="none",
            secret_hint="dry-run",
            is_enabled=True,
            config={"description": "Routes external workflow events to downstream no-code automations."},
        ),
        Integration(
            name="Notification Gateway",
            integration_type=IntegrationType.email,
            status=IntegrationStatus.healthy,
            endpoint=None,
            auth_type="token",
            secret_hint="notif-***",
            is_enabled=True,
            config={"channel": "email-simulation"},
        ),
        Integration(
            name="Internal Ops API",
            integration_type=IntegrationType.internal_api,
            status=IntegrationStatus.healthy,
            endpoint="https://internal-api.example.com/workflows",
            auth_type="service_token",
            secret_hint="ops-***",
            is_enabled=True,
            config={"owner": "platform-ops"},
        ),
    ]
    session.add_all(integrations)
    session.flush()

    seed_definitions = [
        {
            "task_type": TaskType.support,
            "priority": TaskPriority.high,
            "status": TaskStatus.completed,
            "execution_mode": ExecutionMode.autonomous,
            "requester_name": "Nina Patel",
            "requester_email": "nina.patel@example.com",
            "department": "Support",
            "title": "Triaged billing export incident for enterprise customer",
            "description": "Customer reported repeated billing export failures affecting finance reconciliation.",
            "assignee": "Support Operations",
            "decision_text": "Route to Support Operations, open a support case, notify requester, and sync an external incident event.",
            "recommended_tool": "internal_api",
            "confidence": 0.91,
            "resolution_summary": "Support case opened, customer notified, and incident event emitted.",
            "estimated_minutes_saved": 46,
            "needs_review": False,
            "created_at": now - timedelta(days=4),
            "verifier_passed": True,
        },
        {
            "task_type": TaskType.onboarding,
            "priority": TaskPriority.medium,
            "status": TaskStatus.completed,
            "execution_mode": ExecutionMode.semi_autonomous,
            "requester_name": "Lena Cho",
            "requester_email": "lena.cho@example.com",
            "department": "People Ops",
            "title": "Prepared onboarding checklist for new revenue analyst",
            "description": "New analyst starts next Tuesday and needs access bundle, agenda, and manager notification.",
            "assignee": "People Operations",
            "decision_text": "Create the onboarding checklist, provision the access bundle, and notify the hiring manager.",
            "recommended_tool": "task_manager",
            "confidence": 0.87,
            "resolution_summary": "Checklist created and provisioning request sent to internal systems.",
            "estimated_minutes_saved": 58,
            "needs_review": False,
            "created_at": now - timedelta(days=3),
            "verifier_passed": True,
        },
        {
            "task_type": TaskType.internal_ops,
            "priority": TaskPriority.urgent,
            "status": TaskStatus.awaiting_review,
            "execution_mode": ExecutionMode.manual,
            "requester_name": "Mason Green",
            "requester_email": "mason.green@example.com",
            "department": "Operations",
            "title": "Urgent contractor laptop and access provisioning",
            "description": "Contractor starts within 48 hours and requires hardware plus SaaS access.",
            "assignee": "Operations Desk",
            "decision_text": "Assign the request to Operations Desk and hold for human review because of urgent hardware spend.",
            "recommended_tool": "task_manager",
            "confidence": 0.69,
            "resolution_summary": "Pending human approval before procurement execution.",
            "estimated_minutes_saved": 33,
            "needs_review": True,
            "created_at": now - timedelta(days=2),
            "verifier_passed": False,
        },
        {
            "task_type": TaskType.follow_up,
            "priority": TaskPriority.high,
            "status": TaskStatus.awaiting_review,
            "execution_mode": ExecutionMode.autonomous,
            "requester_name": "Sophie Rivera",
            "requester_email": "sophie.rivera@example.com",
            "department": "Customer Success",
            "title": "Follow-up automation for unresolved invoice sync issue",
            "description": "Customer success requested a reminder and escalation path for an overdue integration issue.",
            "assignee": "Customer Success Operations",
            "decision_text": "Send a follow-up note and schedule a reminder, but route to review if verification confidence drops.",
            "recommended_tool": "email",
            "confidence": 0.76,
            "resolution_summary": "Reminder drafted; verifier requested human review before marking complete.",
            "estimated_minutes_saved": 24,
            "needs_review": True,
            "created_at": now - timedelta(days=1),
            "verifier_passed": False,
        },
    ]

    memory_service = MemoryService(session)

    for index, definition in enumerate(seed_definitions, start=1):
        workflow = Workflow(
            name=f"{definition['task_type'].value.replace('_', ' ').title()} Workflow",
            workflow_key=f"{definition['task_type'].value}-flow",
            status=definition["status"],
            current_stage=(
                WorkflowStage.completed
                if definition["status"] == TaskStatus.completed
                else WorkflowStage.review
            ),
            shared_context={
                "seeded": True,
                "task_type": definition["task_type"].value,
                "assignee": definition["assignee"],
            },
            started_at=definition["created_at"],
            completed_at=definition["created_at"] + timedelta(minutes=8)
            if definition["status"] == TaskStatus.completed
            else None,
            created_at=definition["created_at"],
            updated_at=definition["created_at"] + timedelta(minutes=10),
        )
        session.add(workflow)
        session.flush()

        requester = users[index % len(users)]
        task = Task(
            workflow_id=workflow.id,
            requester_id=requester.id,
            title=definition["title"],
            description=definition["description"],
            task_type=definition["task_type"],
            priority=definition["priority"],
            status=definition["status"],
            execution_mode=definition["execution_mode"],
            source="seed",
            requester_name=definition["requester_name"],
            requester_email=definition["requester_email"],
            department=definition["department"],
            confidence=definition["confidence"],
            assignee=definition["assignee"],
            decision_summary=definition["decision_text"],
            resolution_summary=definition["resolution_summary"],
            estimated_minutes_saved=definition["estimated_minutes_saved"],
            latency_ms=640 + (index * 120),
            needs_human_review=definition["needs_review"],
            user_override=False,
            task_metadata={"seeded": True, "index": index},
            created_at=definition["created_at"],
            updated_at=definition["created_at"] + timedelta(minutes=12),
        )
        session.add(task)
        session.flush()

        session.add(
            AgentDecision(
                workflow_id=workflow.id,
                task_id=task.id,
                classification=definition["task_type"].value,
                decision_text=definition["decision_text"],
                action_plan={"steps": [{"tool": definition["recommended_tool"], "operation": "seeded"}]},
                recommended_tool=definition["recommended_tool"],
                confidence=definition["confidence"],
                rationale="Seeded example showcasing a realistic operational routing decision.",
                similar_cases=[
                    {
                        "content": "Prior successful workflow with matching department and task type.",
                        "metadata": {"success": True},
                    }
                ],
                policy_hints=[
                    "Escalate low-confidence or high-spend requests for review.",
                    "Favor previous successful assignee patterns when available.",
                ],
                requires_human_review=definition["needs_review"],
                created_at=definition["created_at"] + timedelta(minutes=1),
            )
        )

        session.add_all(
            [
                ExecutionLog(
                    workflow_id=workflow.id,
                    task_id=task.id,
                    agent_name="Decision Agent",
                    stage="decision",
                    message=definition["decision_text"],
                    payload={"confidence": definition["confidence"]},
                    latency_ms=180,
                    created_at=definition["created_at"] + timedelta(minutes=1),
                ),
                ExecutionLog(
                    workflow_id=workflow.id,
                    task_id=task.id,
                    agent_name="Execution Agent",
                    stage="execution",
                    message=definition["resolution_summary"],
                    payload={"tool": definition["recommended_tool"]},
                    latency_ms=340,
                    created_at=definition["created_at"] + timedelta(minutes=2),
                ),
                ExecutionLog(
                    workflow_id=workflow.id,
                    task_id=task.id,
                    agent_name="Verifier Agent",
                    stage="verification",
                    message=(
                        "Verifier approved the automated execution."
                        if definition["verifier_passed"]
                        else "Verifier requested human review."
                    ),
                    payload={"passed": definition["verifier_passed"]},
                    latency_ms=140,
                    created_at=definition["created_at"] + timedelta(minutes=3),
                ),
            ]
        )

        session.add(
            VerifierResult(
                workflow_id=workflow.id,
                task_id=task.id,
                passed=definition["verifier_passed"],
                confidence=0.89 if definition["verifier_passed"] else 0.58,
                issues=[] if definition["verifier_passed"] else ["Requires human approval due to workflow risk."],
                summary=(
                    "Execution artifacts passed policy and quality checks."
                    if definition["verifier_passed"]
                    else "Hold for review because confidence and spend risk are below policy."
                ),
                recommended_status=(
                    "completed" if definition["verifier_passed"] else "awaiting_review"
                ),
                created_at=definition["created_at"] + timedelta(minutes=3),
            )
        )

        session.add_all(
            [
                FeedbackEvent(
                    workflow_id=workflow.id,
                    task_id=task.id,
                    event_type="execution_success",
                    score=1.0 if definition["status"] == TaskStatus.completed else 0.0,
                    notes="Seeded execution outcome for demo analytics.",
                    payload={"latency_ms": task.latency_ms},
                    created_at=definition["created_at"] + timedelta(minutes=4),
                ),
                FeedbackEvent(
                    workflow_id=workflow.id,
                    task_id=task.id,
                    event_type="reliability_score",
                    score=round((definition["confidence"] + (0.89 if definition["verifier_passed"] else 0.58)) / 2, 2),
                    notes="Seeded blended reliability score.",
                    payload={"task_type": definition["task_type"].value},
                    created_at=definition["created_at"] + timedelta(minutes=5),
                ),
            ]
        )

        session.add_all(
            [
                AgentState(
                    workflow_id=workflow.id,
                    task_id=task.id,
                    agent_name="Decision Agent",
                    stage="decision",
                    state={"assignee": definition["assignee"], "confidence": definition["confidence"]},
                    version=1,
                    created_at=definition["created_at"] + timedelta(minutes=1),
                ),
                AgentState(
                    workflow_id=workflow.id,
                    task_id=task.id,
                    agent_name="Verifier Agent",
                    stage="verification",
                    state={"passed": definition["verifier_passed"]},
                    version=1,
                    created_at=definition["created_at"] + timedelta(minutes=3),
                ),
            ]
        )

        workflow.shared_context = {
            "decision": definition["decision_text"],
            "assignee": definition["assignee"],
            "estimated_minutes_saved": definition["estimated_minutes_saved"],
            "verifier_passed": definition["verifier_passed"],
        }
        memory_service.store_task_memory(
            task,
            "seed_memory",
            memory_service.build_memory_snapshot(task),
            {
                "task_type": definition["task_type"].value,
                "status": definition["status"].value,
                "seeded": True,
            },
        )

    session.commit()

