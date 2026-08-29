from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth import get_current_user
from backend.db.db import get_db
from backend.models.subscription import PlanTier, Subscription, SubscriptionStatus
from backend.models.user import User

_PLAN_RANK = {
    PlanTier.DECOUVERTE: 0,
    PlanTier.PRO: 1,
    PlanTier.BUSINESS: 2,
}

_PLAN_LABEL = {
    PlanTier.DECOUVERTE: "Découverte",
    PlanTier.PRO: "Pro",
    PlanTier.BUSINESS: "Business",
}


async def check_plan_access(
    db: AsyncSession,
    user: User,
    min_tier: PlanTier,
) -> None:
    """Raise 403 if the user's account is below the required plan tier."""
    subscription = (await db.execute(
        select(Subscription).where(Subscription.account_id == user.account_id)
    )).scalars().first()

    if subscription is None or subscription.plan_tier is None:
        effective_tier = PlanTier.DECOUVERTE
    else:
        effective_tier = subscription.plan_tier

    if subscription is None or subscription.status != SubscriptionStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your subscription is not active. Please renew your plan.",
        )

    if _PLAN_RANK[effective_tier] < _PLAN_RANK[min_tier]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"This feature requires the {_PLAN_LABEL[min_tier]} plan or higher.",
        )


def require_plan(min_tier: PlanTier):
    async def checker(
        current_user: Annotated[User, Depends(get_current_user)],
        db: Annotated[AsyncSession, Depends(get_db)],
    ) -> User:
        await check_plan_access(db, current_user, min_tier)
        return current_user

    return checker


async def account_company_limit(db: AsyncSession, user: User) -> int | None:
    """Company limit for the account's plan (None = unlimited, Business)."""
    subscription = (await db.execute(
        select(Subscription).where(Subscription.account_id == user.account_id)
    )).scalars().first()

    if subscription is None or subscription.plan_tier is None:
        return 1
    if _PLAN_RANK[subscription.plan_tier] >= _PLAN_RANK[PlanTier.BUSINESS]:
        return None
    return 1