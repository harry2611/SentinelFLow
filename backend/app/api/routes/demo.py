from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.demo import DemoRunRequest
from app.services.demo_service import DemoService
from app.services.task_service import TaskService


router = APIRouter()


@router.post("/run")
def run_demo(payload: DemoRunRequest, db: Session = Depends(get_db)):
    task_service = TaskService(db)
    demo_service = DemoService(task_service)
    return {
        "created": demo_service.run(payload.template, payload.execution_mode),
        "message": "Demo workflows created and queued for processing.",
    }

