from __future__ import annotations

import hashlib
import math
from collections import Counter
from typing import Any

from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from app.agents.types import DecisionResult, VerificationResult
from app.core.config import get_settings
from app.models.entities import Task, TaskPriority, TaskType


TASK_KEYWORDS: dict[TaskType, set[str]] = {
    TaskType.support: {
        "customer",
        "support",
        "ticket",
        "billing",
        "refund",
        "incident",
        "bug",
        "export",
        "login",
    },
    TaskType.onboarding: {
        "onboard",
        "new hire",
        "employee",
        "laptop",
        "orientation",
        "access",
        "manager",
        "start date",
    },
    TaskType.internal_ops: {
        "ops",
        "vendor",
        "procurement",
        "access request",
        "finance",
        "contractor",
        "policy",
        "internal",
    },
    TaskType.follow_up: {
        "follow up",
        "reminder",
        "unresolved",
        "nudge",
        "overdue",
        "escalate",
        "chase",
        "pending",
    },
}


class LLMService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._llm = None
        self._embeddings = None
        if self.settings.openai_api_key:
            self._llm = ChatOpenAI(
                api_key=self.settings.openai_api_key,
                model=self.settings.openai_model,
                temperature=0,
            )
            self._embeddings = OpenAIEmbeddings(
                api_key=self.settings.openai_api_key,
                model=self.settings.openai_embedding_model,
            )

    @property
    def has_openai(self) -> bool:
        return bool(self._llm and self._embeddings)

    def embed_text(self, text: str) -> list[float]:
        if self._embeddings:
            return self._embeddings.embed_query(text)
        return self._deterministic_embedding(text)

    def generate_decision(
        self,
        task: Task,
        similar_cases: list[dict[str, Any]],
        policy_hints: list[str],
    ) -> DecisionResult:
        if self._llm:
            prompt = self._build_decision_prompt(task, similar_cases, policy_hints)
            try:
                response = self._llm.invoke(prompt)
                return self._parse_decision_response(
                    task=task,
                    text=getattr(response, "content", str(response)),
                    similar_cases=similar_cases,
                    policy_hints=policy_hints,
                )
            except Exception:
                pass
        return self._heuristic_decision(task, similar_cases, policy_hints)

    def verify_execution(
        self,
        task: Task,
        decision: DecisionResult,
        execution_summary: dict[str, Any],
    ) -> VerificationResult:
        if self._llm:
            prompt = self._build_verifier_prompt(task, decision, execution_summary)
            try:
                response = self._llm.invoke(prompt)
                return self._parse_verifier_response(
                    text=getattr(response, "content", str(response)),
                    execution_summary=execution_summary,
                )
            except Exception:
                pass
        return self._heuristic_verification(task, decision, execution_summary)

    def _build_decision_prompt(
        self,
        task: Task,
        similar_cases: list[dict[str, Any]],
        policy_hints: list[str],
    ) -> str:
        return f"""
You are SentinelFlow's decision agent.
Classify and route the task, decide the action plan, assign an owner, and estimate confidence.

Task
- title: {task.title}
- description: {task.description}
- priority: {task.priority.value}
- department: {task.department}
- mode: {task.execution_mode.value}

Similar successful cases:
{similar_cases}

Policy hints:
{policy_hints}

Return a concise response with:
classification:
assignee:
confidence:
decision:
rationale:
steps:
"""

    def _build_verifier_prompt(
        self,
        task: Task,
        decision: DecisionResult,
        execution_summary: dict[str, Any],
    ) -> str:
        return f"""
You are SentinelFlow's verifier agent.
Review whether the execution outcome satisfies the task, whether confidence is high enough,
and whether human review is required.

Task: {task.title}
Description: {task.description}
Decision: {decision.model_dump()}
Execution: {execution_summary}

Return:
passed:
confidence:
issues:
summary:
recommended_status:
"""

    def _parse_decision_response(
        self,
        task: Task,
        text: str,
        similar_cases: list[dict[str, Any]],
        policy_hints: list[str],
    ) -> DecisionResult:
        task_type = self._classify_text(f"{task.title} {task.description}")
        confidence = min(0.94, 0.68 + 0.04 * len(similar_cases) + 0.02 * len(policy_hints))
        return self._heuristic_decision(task, similar_cases, policy_hints).model_copy(
            update={
                "classification": task_type.value,
                "decision_text": text.splitlines()[0][:240] if text else "LLM route generated.",
                "confidence": confidence,
                "rationale": text[:600] if text else "Routed from OpenAI-generated plan.",
            }
        )

    def _parse_verifier_response(
        self, text: str, execution_summary: dict[str, Any]
    ) -> VerificationResult:
        success = execution_summary.get("success", False)
        issues = [] if success else ["Execution output reported a tool failure."]
        return VerificationResult(
            passed=success,
            confidence=0.88 if success else 0.48,
            issues=issues,
            summary=text[:400] if text else "Verifier completed review.",
            recommended_status="completed" if success else "awaiting_review",
        )

    def _heuristic_decision(
        self,
        task: Task,
        similar_cases: list[dict[str, Any]],
        policy_hints: list[str],
    ) -> DecisionResult:
        detected_type = self._classify_text(f"{task.title} {task.description}")
        base_confidence = 0.62 + 0.06 * min(len(similar_cases), 3) + 0.03 * min(
            len(policy_hints), 2
        )
        if task.priority in {TaskPriority.high, TaskPriority.urgent}:
            base_confidence += 0.04
        if task.execution_mode.value == "manual":
            base_confidence -= 0.08

        assignee, recommended_tool, action_plan, labels, time_saved = self._build_plan(
            detected_type, task
        )
        confidence = max(0.45, min(base_confidence, 0.93))
        requires_review = task.execution_mode.value == "manual" or confidence < 0.72
        rationale = (
            f"Classified as {detected_type.value} based on request keywords, department context, "
            f"and {len(similar_cases)} similar retrieved runs."
        )
        if policy_hints:
            rationale += f" Applied policy hints: {'; '.join(policy_hints[:2])}."

        decision_text = (
            f"Route to {assignee} and execute the {detected_type.value.replace('_', ' ')} "
            f"playbook with {recommended_tool} as the primary tool."
        )
        return DecisionResult(
            classification=detected_type.value,
            decision_text=decision_text,
            action_plan=action_plan,
            recommended_tool=recommended_tool,
            confidence=round(confidence, 2),
            rationale=rationale,
            assignee=assignee,
            estimated_minutes_saved=time_saved,
            requires_human_review=requires_review,
            labels=labels,
        )

    def _heuristic_verification(
        self,
        task: Task,
        decision: DecisionResult,
        execution_summary: dict[str, Any],
    ) -> VerificationResult:
        tool_runs = execution_summary.get("tool_runs", [])
        failed_runs = [run for run in tool_runs if not run.get("success", False)]
        issues = []
        if failed_runs:
            issues.append("One or more tools returned a degraded or failed result.")
        if decision.confidence < self.settings.verifier_pass_threshold:
            issues.append("Decision confidence remained below the verifier threshold.")
        if not execution_summary.get("success", False):
            issues.append("Execution agent reported an unsuccessful outcome.")
        passed = not issues
        return VerificationResult(
            passed=passed,
            confidence=0.9 if passed else 0.55,
            issues=issues,
            summary=(
                "Execution satisfied the requested workflow and produced the expected artifacts."
                if passed
                else "Verifier recommends human review before completion."
            ),
            recommended_status="completed" if passed else "awaiting_review",
        )

    def _classify_text(self, text: str) -> TaskType:
        lowered = text.lower()
        scores = {
            task_type: sum(1 for keyword in keywords if keyword in lowered)
            for task_type, keywords in TASK_KEYWORDS.items()
        }
        winner, score = Counter(scores).most_common(1)[0]
        return winner if score > 0 else TaskType.internal_ops

    def _build_plan(self, task_type: TaskType, task: Task) -> tuple[str, str, dict[str, Any], list[str], int]:
        metadata = task.task_metadata or {}
        if task_type == TaskType.support:
            queue = "tier-2-billing" if "billing" in task.description.lower() else "support-general"
            return (
                "Support Operations",
                "internal_api",
                {
                    "steps": [
                        {
                            "tool": "internal_api",
                            "operation": "create_support_case",
                            "queue": queue,
                            "priority": task.priority.value,
                        },
                        {
                            "tool": "email",
                            "operation": "notify_requester",
                            "recipient": task.requester_email,
                            "template": "support_triage",
                        },
                        {
                            "tool": "zapier",
                            "operation": "emit_workflow_event",
                            "enabled": metadata.get("notify_external", True),
                        },
                    ]
                },
                ["support", "sla"],
                42,
            )
        if task_type == TaskType.onboarding:
            return (
                "People Operations",
                "task_manager",
                {
                    "steps": [
                        {
                            "tool": "task_manager",
                            "operation": "create_checklist",
                            "items": [
                                "Provision identity access",
                                "Prepare onboarding agenda",
                                "Notify manager with start-day checklist",
                            ],
                        },
                        {
                            "tool": "internal_api",
                            "operation": "provision_access_bundle",
                            "bundle": metadata.get("access_bundle", "core-saas"),
                        },
                        {
                            "tool": "email",
                            "operation": "notify_manager",
                            "recipient": metadata.get("manager_email", task.requester_email),
                            "template": "onboarding_ready",
                        },
                    ]
                },
                ["people", "checklist"],
                55,
            )
        if task_type == TaskType.follow_up:
            return (
                "Customer Success Operations",
                "email",
                {
                    "steps": [
                        {
                            "tool": "email",
                            "operation": "send_follow_up",
                            "recipient": metadata.get("recipient_email", task.requester_email),
                            "template": "follow_up_unresolved",
                        },
                        {
                            "tool": "task_manager",
                            "operation": "schedule_follow_up",
                            "days_until_due": metadata.get("days_until_due", 2),
                        },
                        {
                            "tool": "zapier",
                            "operation": "emit_workflow_event",
                            "enabled": True,
                        },
                    ]
                },
                ["follow-up", "retention"],
                28,
            )
        return (
            "Operations Desk",
            "task_manager",
            {
                "steps": [
                    {
                        "tool": "task_manager",
                        "operation": "assign_internal_owner",
                        "owner": "ops-queue",
                    },
                    {
                        "tool": "internal_api",
                        "operation": "create_ops_ticket",
                        "department": task.department,
                    },
                    {
                        "tool": "email",
                        "operation": "notify_requester",
                        "recipient": task.requester_email,
                        "template": "ops_ack",
                    },
                ]
            },
            ["ops", "routing"],
            35,
        )

    def _deterministic_embedding(self, text: str) -> list[float]:
        text = text or "sentinelflow"
        values: list[float] = []
        cursor = hashlib.sha256(text.encode("utf-8")).digest()
        while len(values) < self.settings.openai_embedding_dimensions:
            cursor = hashlib.sha256(cursor + text.encode("utf-8")).digest()
            for byte in cursor:
                values.append((byte / 127.5) - 1)
                if len(values) >= self.settings.openai_embedding_dimensions:
                    break
        norm = math.sqrt(sum(value * value for value in values)) or 1.0
        return [round(value / norm, 8) for value in values]

