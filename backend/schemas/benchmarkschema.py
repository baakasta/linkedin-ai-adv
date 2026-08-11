import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class BenchmarkCreate(BaseModel):
    company_id: uuid.UUID
    audit_ids: list[uuid.UUID] = Field(min_length=1)


class BenchmarkResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    audit_ids: list
    resultat: dict
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
