"""Per-plan AI usage quotas, enforced on AI creates (audits, optimizations,
generations, strategies). Quotas reset each calendar month (UTC). None = unlimited.
Feature keys are used by enforce_ai_quota() and documented in the README."""

from datetime import UTC, datetime
import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.audit import Audit
from backend.models.company import Company
from backend.models.generation import Generation
from backend.models.optimization import Optimization
from backend.models.recommendation import Recommendation
from backend.models.strategy import Strategy
from backend.models.subscription import PlanTier, Subscription

AI_QUOTAS: dict[PlanTier, dict[str, int | None]] = {
    PlanTier.DECOUVERTE: {
        "audits": 5,
        "optimizations": 5,
        "generations": 3,
        "strategies": 1,
    },
    PlanTier.PRO: {
        "audits": None,
        "optimizations": None,
        "generations": None,
        "strategies": None,
    },
    PlanTier.BUSINESS: {
        "audits": None,
        "optimizations": None,
        "generations": None,
        "strategies": None,
    },
}

_FEATURE_LABELS = {
    "audits": "audits",
    "optimizations": "optimizations",
    "generations": "content generations",
    "strategies": "strategies",
}


async def _account_company_ids(db: AsyncSession, user) -> list[uuid.UUID]:
    result = await db.execute(
        select(Company.id).where(Company.account_id == user.account_id)
    )
    return list(result.scalars().all())


async def count_feature_usage(db: AsyncSession, user, feature: str) -> int:
    company_ids = await _account_company_ids(db, user)
    if not company_ids:
        return 0

    now = datetime.now(UTC)
    month_start = datetime(now.year, now.month, 1, tzinfo=UTC)

    if feature == "audits":
        stmt = select(func.count()).select_from(Audit).where(
            Audit.company_id.in_(company_ids),
            Audit.created_at >= month_start,
        )
    elif feature == "optimizations":
        stmt = (
            select(func.count())
            .select_from(Optimization)
            .join(Recommendation, Recommendation.id == Optimization.recommendation_id)
            .join(Audit, Audit.id == Recommendation.audit_id)
            .where(Audit.company_id.in_(company_ids), Optimization.created_at >= month_start)
        )
    elif feature == "generations":
        stmt = select(func.count()).select_from(Generation).where(
            Generation.company_id.in_(company_ids),
            Generation.created_at >= month_start,
        )
    elif feature == "strategies":
        stmt = select(func.count()).select_from(Strategy).where(
            Strategy.company_id.in_(company_ids),
            Strategy.created_at >= month_start,
        )
    else:
        raise ValueError(f"Unknown quota feature: {feature}")

    return (await db.execute(stmt)).scalar_one()


async def enforce_ai_quota(db: AsyncSession, user, feature: str) -> None:
    """Raise 403 when the account's monthly quota for the feature is exhausted."""
    subscription = (await db.execute(
        select(Subscription).where(Subscription.account_id == user.account_id)
    )).scalars().first()

    tier = subscription.plan_tier if subscription and subscription.plan_tier else PlanTier.DECOUVERTE
    limit = AI_QUOTAS.get(tier, AI_QUOTAS[PlanTier.DECOUVERTE]).get(feature)

    if limit is None:
        return

    used = await count_feature_usage(db, user, feature)
    if used >= limit:
        label = _FEATURE_LABELS.get(feature, feature)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Monthly quota reached ({used}/{limit} {label}) on the "
                f"{tier.value} plan. Upgrade to unlock more."
            ),
        )