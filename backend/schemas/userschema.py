import uuid
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class AccountResponse(BaseModel):
    id: uuid.UUID
    name: str
    model_config = ConfigDict(from_attributes=True)


class UserBase(BaseModel):
    full_name: str = Field(min_length=1, max_length=50)
    email: EmailStr = Field(max_length=120)


class UserCreate(UserBase):
    account_name: str = Field(min_length=1, max_length=255)


class UserResponse(UserBase):
    id: uuid.UUID
    account_id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)