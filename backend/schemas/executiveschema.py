import uuid
from pydantic import BaseModel, ConfigDict, Field

class ExecutiveBase(BaseModel):
    company_id: uuid.UUID
    full_name: str = Field(min_length=1, max_length=255)
    job_title: str | None = Field(default=None, min_length=1, max_length=120)
    linkedin_url: str | None = None

class ExecutiveCreate(ExecutiveBase):
    pass


class ExecutiveResponse(ExecutiveBase):
    id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)

class ExecutiveUpdate(BaseModel):
    company_id: uuid.UUID | None = None
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    job_title: str | None = Field(default=None, min_length=1, max_length=120)
    linkedin_url: str | None = None