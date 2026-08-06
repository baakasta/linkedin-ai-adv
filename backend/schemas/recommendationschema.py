import uuid
from pydantic import BaseModel, ConfigDict
from backend.models.recommendation import RecommendationPriority


class RecommendationResponse(BaseModel):
    id: uuid.UUID
    audit_id: uuid.UUID
    critere_code: str
    categorie: str
    priorite: RecommendationPriority
    action: str
    raison: str
    model_config = ConfigDict(from_attributes=True)