import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AuditCreate(BaseModel):
    company_id: uuid.UUID
    linkedin_data: dict  # raw LinkedIn JSON sent to AI


class AuditResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    score_global: int
    score_entreprise: int
    score_dirigeant: int | None
    dirigeant_present: bool
    score_detail: dict
    analyse_ia: dict
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class AuditListResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    score_global: int
    score_entreprise: int
    score_dirigeant: int | None
    dirigeant_present: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)