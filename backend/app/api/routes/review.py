from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.common import TaskSummary
from app.schemas.task import ReviewAction, TaskDetailResponse
from app.services.task_service import TaskService


router = APIRouter()


@router.get("/queue", response_model=list[TaskSummary])
def get_review_queue(db: Session = Depends(get_db)):
    service = TaskService(db)
    return service.get_review_queue()


@router.post("/{task_id}/approve", response_model=TaskDetailResponse)
def approve_task(task_id: UUID, payload: ReviewAction, db: Session = Depends(get_db)):
    service = TaskService(db)
    try:
        task, _queue = service.approve_task(task_id, payload)
        return task
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{task_id}/reject", response_model=TaskDetailResponse)
def reject_task(task_id: UUID, payload: ReviewAction, db: Session = Depends(get_db)):
    service = TaskService(db)
    try:
        return service.reject_task(task_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

