import uuid
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict


class ReportShareCreate(BaseModel):
    company_id: uuid.UUID
    expires_at: date | None = None


class ReportShareResponse(BaseModel):
    id: uuid.UUID
    token: str
    scope: str
    company_id: uuid.UUID
    audit_id: uuid.UUID | None = None
    benchmark_id: uuid.UUID | None = None
    month: str | None = None
    expires_at: datetime | None = None
    revoked: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ReportShareUrl(BaseModel):
    token: str
    url: str
    expires_at: datetime | None = None


class HistoryEntry(BaseModel):
    id: uuid.UUID | None = None
    type: str
    titre: str
    created_at: datetime | None = None
    month: str | None = None
    url: str


class ReportHistory(BaseModel):
    reports: list[HistoryEntry]
