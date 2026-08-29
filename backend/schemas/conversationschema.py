import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class ConversationCreate(BaseModel):
    company_id: uuid.UUID
    title: str | None = Field(default=None, max_length=255)


class ConversationResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    title: str | None = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class AssistantMessageRequest(BaseModel):
    content: str = Field(min_length=1)


class AssistantMessageResponse(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    author: str
    content: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ConversationDetail(ConversationResponse):
    messages: list[AssistantMessageResponse] = []
