import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class GenerationCreate(BaseModel):
    company_id: uuid.UUID
    type_contenu: str
    brief: dict
    contexte_entreprise: dict


class GenerationResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    type_contenu: str
    brief: dict
    variantes: dict
    marqueurs_a_completer: list | None
    created_at: datetime
    titre_interne: str | None = None
    model_config = ConfigDict(from_attributes=True)