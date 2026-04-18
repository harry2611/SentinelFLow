from pydantic import BaseModel

from app.models.entities import ExecutionMode, TaskType


class DemoRunRequest(BaseModel):
    template: TaskType | None = None
    execution_mode: ExecutionMode = ExecutionMode.semi_autonomous

