from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.common import TaskSummary
from app.schemas.task import TaskCreate, TaskCreateResponse, TaskDetailResponse
from app.services.task_service import TaskService


router = APIRouter()


@router.post("", response_model=TaskCreateResponse)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    service = TaskService(db)
    task, queue = service.create_task(payload)
    return {"task": task, "queue": queue}


@router.get("", response_model=list[TaskSummary])
def list_tasks(
    status: str | None = Query(default=None),
    task_type: str | None = Query(default=None),
    search: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    service = TaskService(db)
    return service.list_tasks(status=status, task_type=task_type, search=search)


@router.get("/{task_id}", response_model=TaskDetailResponse)
def get_task(task_id: UUID, db: Session = Depends(get_db)):
    service = TaskService(db)
    try:
        return service.get_task(task_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

