from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from sqlalchemy.orm import Session

from app.models.entities import Integration, Task


class AgentTool(ABC):
    name: str

    @abstractmethod
    def execute(
        self,
        db: Session,
        task: Task,
        step: dict[str, Any],
        integrations: dict[str, Integration],
    ) -> dict[str, Any]:
        raise NotImplementedError

