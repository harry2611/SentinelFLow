from typing import Any

from pydantic import BaseModel


class AnalyticsOverviewResponse(BaseModel):
    headline_metrics: dict[str, Any]
    status_counts: dict[str, int]
    type_counts: dict[str, int]
    resolution_trends: list[dict[str, Any]]
    recent_decisions: list[dict[str, Any]]
    recent_traces: list[dict[str, Any]]
    memory_retrieval_examples: list[dict[str, Any]]

