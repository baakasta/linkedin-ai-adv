import uuid
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from backend.models.user import UserRole


class AccountResponse(BaseModel):
    id: uuid.UUID
    name: str
    model_config = ConfigDict(from_attributes=True)

class AccountUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=50)



class UserBase(BaseModel):
    full_name: str = Field(min_length=1, max_length=50)
    email: EmailStr = Field(max_length=120)


class UserCreate(UserBase):
    account_name: str = Field(min_length=1, max_length=255)


class UserResponse(UserBase):
    id: uuid.UUID
    account_id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)

class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=50)
    email: EmailStr| None = Field(default=None, max_length=120)
    role: UserRole | None = None
    is_active: bool | None = None
