from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.task import TaskCreate, TaskCreateResponse
from app.services.task_service import TaskService


router = APIRouter()


@router.post("/zapier", response_model=TaskCreateResponse)
def ingest_zapier_webhook(
    payload: TaskCreate,
    db: Session = Depends(get_db),
    x_zapier_source: str | None = Header(default=None),
):
    enriched_payload = payload.model_copy(
        update={
            "source": x_zapier_source or "zapier_webhook",
            "auto_process": True,
        }
    )
    task, queue = TaskService(db).create_task(enriched_payload)
    return {"task": task, "queue": queue}

