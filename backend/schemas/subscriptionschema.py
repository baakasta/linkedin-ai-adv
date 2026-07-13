import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from backend.models.subscription import PlanTier, SubscriptionStatus


class SubscriptionResponse(BaseModel):
    id: uuid.UUID
    account_id: uuid.UUID
    plan_tier: PlanTier
    status: SubscriptionStatus
    current_period_end: datetime | None
    model_config = ConfigDict(from_attributes=True)

class SubscriptionUpdate(BaseModel):
    plan_tier: PlanTier | None = None
    status: SubscriptionStatus | None = None