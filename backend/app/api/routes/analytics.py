from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.analytics import AnalyticsOverviewResponse
from app.services.analytics_service import AnalyticsService


router = APIRouter()


@router.get("/overview", response_model=AnalyticsOverviewResponse)
def get_analytics_overview(db: Session = Depends(get_db)):
    return AnalyticsService(db).get_overview()

