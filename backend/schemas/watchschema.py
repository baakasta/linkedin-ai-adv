import uuid
from datetime import datetime, date
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field


class WatchStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"


class AlertType(str, Enum):
    SCORE_DROP = "score_drop"
    SCORE_IMPROVE = "score_improve"
    COMPETITOR_GROWTH = "competitor_growth"
    ENGAGEMENT_SPIKE = "engagement_spike"
    ENGAGEMENT_DROP = "engagement_drop"
    TREND_DETECTED = "trend_detected"
    OPPORTUNITY = "opportunity"


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class WatchCreate(BaseModel):
    company_id: uuid.UUID
    competitor_ids: list[uuid.UUID] = Field(default_factory=list)


class WatchUpdate(BaseModel):
    competitor_ids: list[uuid.UUID] | None = None
    status: WatchStatus | None = None


class WatchSnapshotResponse(BaseModel):
    id: uuid.UUID
    audit_id: uuid.UUID | None
    period: date
    metrics: dict
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class WatchAlertResponse(BaseModel):
    id: uuid.UUID
    alert_type: AlertType
    title: str
    detail: str | None
    severity: AlertSeverity
    read: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class WatchResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    competitor_ids: list | None
    frequency: str
    status: str
    latest_snapshot: WatchSnapshotResponse | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class VeilleOverview(BaseModel):
    watch_id: uuid.UUID
    company_id: uuid.UUID
    latest_snapshot: WatchSnapshotResponse | None
    competitor_snapshots: list[dict]
    recent_alerts: list[WatchAlertResponse]
    ai_analysis: str | None
