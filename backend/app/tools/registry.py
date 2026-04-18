from __future__ import annotations

from app.tools.base import AgentTool
from app.tools.builtins import EmailSimulationTool, InternalApiTool, TaskManagerTool, ZapierWebhookTool


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, AgentTool] = {
            InternalApiTool.name: InternalApiTool(),
            EmailSimulationTool.name: EmailSimulationTool(),
            TaskManagerTool.name: TaskManagerTool(),
            ZapierWebhookTool.name: ZapierWebhookTool(),
        }

    def get(self, tool_name: str) -> AgentTool:
        if tool_name not in self._tools:
            raise KeyError(f"Unknown tool requested: {tool_name}")
        return self._tools[tool_name]

    def list_names(self) -> list[str]:
        return sorted(self._tools.keys())

