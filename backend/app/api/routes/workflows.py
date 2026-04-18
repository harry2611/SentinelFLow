from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.models.entities import Workflow
from app.schemas.task import WorkflowDetailResponse


router = APIRouter()


@router.get("/{workflow_id}", response_model=WorkflowDetailResponse)
def get_workflow(workflow_id: UUID, db: Session = Depends(get_db)):
    workflow = db.scalar(
        select(Workflow)
        .where(Workflow.id == workflow_id)
        .options(
            selectinload(Workflow.task),
            selectinload(Workflow.execution_logs),
            selectinload(Workflow.states),
        )
    )
    if not workflow or not workflow.task:
        raise HTTPException(status_code=404, detail="Workflow not found")
    workflow.execution_logs.sort(key=lambda row: row.created_at)
    workflow.states.sort(key=lambda row: row.created_at)
    return {
        "id": workflow.id,
        "name": workflow.name,
        "workflow_key": workflow.workflow_key,
        "status": workflow.status,
        "current_stage": workflow.current_stage,
        "shared_context": workflow.shared_context,
        "started_at": workflow.started_at,
        "completed_at": workflow.completed_at,
        "task_id": workflow.task.id,
        "execution_logs": workflow.execution_logs,
        "agent_states": workflow.states,
    }
