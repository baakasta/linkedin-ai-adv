import uuid
from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict


class FreqEnum(int, Enum):
    J30 = 30
    J60 = 60
    J90 = 90


class CalendarCreate(BaseModel):
    company_id: uuid.UUID
    frequence: FreqEnum = FreqEnum.J30


class CalendarUpdate(BaseModel):
    frequence: FreqEnum


class CalendarSlotResponse(BaseModel):
    id: uuid.UUID
    date: date
    type_contenu: str
    sujet: str | None = None
    objectif: str | None = None
    cta: str | None = None
    status: str
    generation_id: uuid.UUID | None = None
    model_config = ConfigDict(from_attributes=True)


class CalendarResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    frequence: int
    slots: list[CalendarSlotResponse] = []
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
