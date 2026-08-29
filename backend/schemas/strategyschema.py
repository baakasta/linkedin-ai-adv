import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class StrategyCreate(BaseModel):
    company_id: uuid.UUID
    audit_id: uuid.UUID | None = None


class StrategyResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    audit_id: uuid.UUID | None = None
    resultat: dict
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
