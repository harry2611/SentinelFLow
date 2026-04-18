from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.integration import IntegrationResponse, IntegrationTestResponse, IntegrationUpdate
from app.services.integration_service import IntegrationService


router = APIRouter()


@router.get("", response_model=list[IntegrationResponse])
def list_integrations(db: Session = Depends(get_db)):
    return IntegrationService(db).list_integrations()


@router.put("/{integration_id}", response_model=IntegrationResponse)
def update_integration(
    integration_id: UUID, payload: IntegrationUpdate, db: Session = Depends(get_db)
):
    service = IntegrationService(db)
    try:
        integration = service.get_integration(integration_id)
        return service.update_integration(integration, payload.model_dump(exclude_unset=True))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{integration_id}/test", response_model=IntegrationTestResponse)
def test_integration(integration_id: UUID, db: Session = Depends(get_db)):
    service = IntegrationService(db)
    try:
        integration = service.get_integration(integration_id)
        return service.test_integration(integration)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

