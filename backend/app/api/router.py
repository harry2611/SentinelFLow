from fastapi import APIRouter

from app.api.routes.analytics import router as analytics_router
from app.api.routes.demo import router as demo_router
from app.api.routes.integrations import router as integrations_router
from app.api.routes.review import router as review_router
from app.api.routes.tasks import router as tasks_router
from app.api.routes.webhooks import router as webhooks_router
from app.api.routes.workflows import router as workflows_router


api_router = APIRouter()
api_router.include_router(tasks_router, prefix="/tasks", tags=["tasks"])
api_router.include_router(workflows_router, prefix="/workflows", tags=["workflows"])
api_router.include_router(review_router, prefix="/review", tags=["review"])
api_router.include_router(analytics_router, prefix="/analytics", tags=["analytics"])
api_router.include_router(integrations_router, prefix="/integrations", tags=["integrations"])
api_router.include_router(demo_router, prefix="/demo", tags=["demo"])
api_router.include_router(webhooks_router, prefix="/webhooks", tags=["webhooks"])

