import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class OptimizationCreate(BaseModel):
    recommendation_id: uuid.UUID
    type_element: str
    contenu_original: str | None = None
    contexte_entreprise: dict


class OptimizationResponse(BaseModel):
    id: uuid.UUID
    recommendation_id: uuid.UUID
    type_element: str
    contenu_original: str | None
    variantes: dict          # contains the full variantes array
    variante_recommandee: dict
    marqueurs: list | None
    faiblesses_corrigees: list | None
    ameliorations_apportees: list | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)