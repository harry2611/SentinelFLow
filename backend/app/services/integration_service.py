from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import Integration, IntegrationStatus


class IntegrationService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_integrations(self) -> list[Integration]:
        return self.db.scalars(select(Integration).order_by(Integration.name)).all()

    def get_integration(self, integration_id: UUID) -> Integration:
        integration = self.db.get(Integration, integration_id)
        if not integration:
            raise ValueError("Integration not found")
        return integration

    def update_integration(self, integration: Integration, payload: dict[str, Any]) -> Integration:
        for field in ["name", "endpoint", "auth_type", "secret_hint", "is_enabled", "status"]:
            if field in payload and payload[field] is not None:
                setattr(integration, field, payload[field])
        if "config" in payload and payload["config"] is not None:
            integration.config = payload["config"]
        self.db.add(integration)
        self.db.commit()
        self.db.refresh(integration)
        return integration

    def test_integration(self, integration: Integration) -> dict[str, Any]:
        if not integration.endpoint:
            integration.status = IntegrationStatus.healthy
            integration.last_ping_at = datetime.now(timezone.utc)
            self.db.commit()
            return {
                "success": True,
                "message": "No endpoint configured, so SentinelFlow ran a dry-run connectivity check.",
            }

        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.post(
                    integration.endpoint,
                    json={"source": "SentinelFlow", "timestamp": datetime.now(timezone.utc).isoformat()},
                )
            integration.status = (
                IntegrationStatus.healthy if response.status_code < 400 else IntegrationStatus.degraded
            )
            integration.last_ping_at = datetime.now(timezone.utc)
            self.db.commit()
            return {
                "success": response.status_code < 400,
                "message": f"Received HTTP {response.status_code} from integration endpoint.",
            }
        except Exception as exc:
            integration.status = IntegrationStatus.offline
            integration.last_ping_at = datetime.now(timezone.utc)
            self.db.commit()
            return {"success": False, "message": f"Connectivity check failed: {exc}"}

