import uuid
from datetime import datetime
from pydantic import BaseModel


class ScoreEvolution(BaseModel):
    date: datetime
    score_global: int
    score_entreprise: int
    score_dirigeant: int | None


class PublicationMetrics(BaseModel):
    total_publications: int
    total_reactions: int
    total_comments: int
    total_shares: int
    avg_engagement: float


class RecommendationsPriority(BaseModel):
    critique: int
    importante: int
    optimisation: int


class OptimizationProgression(BaseModel):
    total: int
    accepted: int
    modified: int
    rejected: int
    pending: int


class ObjectivesTracking(BaseModel):
    score_improvement: int | None
    total_recommendations: int
    total_optimizations: int
    completion_rate: float


class DashboardResponse(BaseModel):
    company_id: uuid.UUID
    linkedin_score: int | None
    score_evolution: list[ScoreEvolution]
    engagement: PublicationMetrics
    publication_frequency: int
    recommendations_priority: RecommendationsPriority
    optimization_progression: OptimizationProgression
    objectives_tracking: ObjectivesTracking
