from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.entities import IntegrationStatus, IntegrationType


class IntegrationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    integration_type: IntegrationType
    status: IntegrationStatus
    endpoint: str | None = None
    auth_type: str | None = None
    secret_hint: str | None = None
    is_enabled: bool
    config: dict[str, Any]
    last_ping_at: datetime | None = None
    updated_at: datetime


class IntegrationUpdate(BaseModel):
    name: str | None = None
    endpoint: str | None = None
    auth_type: str | None = None
    secret_hint: str | None = None
    is_enabled: bool | None = None
    status: IntegrationStatus | None = None
    config: dict[str, Any] | None = None


class IntegrationTestResponse(BaseModel):
    success: bool
    message: str

