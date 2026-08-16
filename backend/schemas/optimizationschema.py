import uuid
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field
from backend.schemas.recommendationschema import RecommendationResponse


class OptimizationCreate(BaseModel):
    recommendation_id: uuid.UUID
    type_element: str
    contenu_original: str | None = None
    contexte_entreprise: dict


class OptimizationDecision(str, Enum):
    ACCEPT = "accept"
    MODIFY = "modify"
    REJECT = "reject"


class OptimizationVerdict(BaseModel):
    optimization_id: uuid.UUID
    decision: OptimizationDecision
    prompt: str | None = None


class OptimizationDecisionRequest(BaseModel):
    verdicts: list[OptimizationVerdict] = Field(min_length=1)


class OptimizationVerdictResult(BaseModel):
    optimization_id: uuid.UUID
    decision: OptimizationDecision
    status: str  # "success" | "error"
    message: str
    result: dict | None = None


class OptimizationResponse(BaseModel):
    id: uuid.UUID
    recommendation_id: uuid.UUID
    type_element: str
    contenu_original: str | None
    contexte_entreprise: dict | None
    variantes: dict          # contains the full variantes array
    variante_recommandee: dict
    marqueurs: list | None
    faiblesses_corrigees: list | None
    ameliorations_apportees: list | None
    decision: str | None
    contenu_final: str | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class RecommendationOptimizations(RecommendationResponse):
    optimizations: list[OptimizationResponse]