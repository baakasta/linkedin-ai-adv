import uuid
from pydantic import BaseModel, ConfigDict, Field

class CompanyBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    linkedin_url: str | None = None

class CompanyCreate(CompanyBase):
    pass

class CompanyResponse(CompanyBase):
    id: uuid.UUID
    account_id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)

class CompanyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    linkedin_url: str | None = None