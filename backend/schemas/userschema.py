import uuid
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from backend.models.user import UserRole


class AccountResponse(BaseModel):
    id: uuid.UUID
    name: str
    model_config = ConfigDict(from_attributes=True)

class AccountUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=50)



class UserBase(BaseModel):
    full_name: str = Field(min_length=1, max_length=50)
    email: EmailStr = Field(max_length=120)


class UserCreate(UserBase):
    account_name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8)


class UserPublic(BaseModel):
    id: uuid.UUID
    full_name: str = Field(min_length=1, max_length=50)
    account_id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)

class UserPrivate(UserPublic):
    email: EmailStr

class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=50)
    email: EmailStr| None = Field(default=None, max_length=120)

class AdminUserUpdate(BaseModel):
    role: UserRole | None = None
    is_active: bool | None = None

class Token(BaseModel):
    access_token: str
    token_type: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr = Field(max_length=120)


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)