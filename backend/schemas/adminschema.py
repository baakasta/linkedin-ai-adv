import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from backend.models.subscription import PlanTier, SubscriptionStatus
from backend.models.user import UserRole


class AdminUserResponse(BaseModel):
    id: uuid.UUID
    full_name: str
    email: str
    role: UserRole
    is_active: bool
    account_id: uuid.UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class AdminAccountResponse(BaseModel):
    id: uuid.UUID
    name: str
    created_at: datetime
    users: list[AdminUserResponse] = []
    companies: list["AdminCompanyResponse"] = []
    subscription: "AdminSubscriptionResponse | None" = None
    model_config = ConfigDict(from_attributes=True)


class AdminCompanyResponse(BaseModel):
    id: uuid.UUID
    name: str
    linkedin_url: str | None = None
    account_id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)


class AdminExecutiveResponse(BaseModel):
    id: uuid.UUID
    full_name: str
    job_title: str | None = None
    linkedin_url: str | None = None
    company_id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)


class AdminSubscriptionResponse(BaseModel):
    id: uuid.UUID
    account_id: uuid.UUID
    plan_tier: PlanTier
    status: SubscriptionStatus
    current_period_end: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


class AdminStats(BaseModel):
    total_users: int
    active_users: int
    total_accounts: int
    total_companies: int
    total_executives: int
    total_audits: int
    total_optimizations: int
    total_generations: int
    total_benchmarks: int
    total_watches: int
    subscriptions_by_tier: dict[str, int]
    subscriptions_by_status: dict[str, int]


class AccountUsage(BaseModel):
    account_id: uuid.UUID
    account_name: str
    plan_tier: PlanTier
    audit_count: int
    optimization_count: int
    generation_count: int
    benchmark_count: int
    watch_count: int
