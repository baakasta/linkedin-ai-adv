from typing import Annotated
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from backend.db.db import get_db
from backend.models.user import User, Account, UserRole
from backend.models.company import Company
from backend.models.executive import Executive
from backend.models.subscription import Subscription
from backend.schemas.userschema import AdminUserUpdate, UserPrivate
from backend.schemas.subscriptionschema import SubscriptionResponse, SubscriptionUpdate
from backend.schemas.companyschema import CompanyResponse
from backend.schemas.executiveschema import ExecutiveResponse
from backend.schemas.adminschema import (
    AdminUserResponse,
    AdminAccountResponse,
    AdminCompanyResponse,
    AdminExecutiveResponse,
    AdminSubscriptionResponse,
    AdminStats,
    AccountUsage,
)
from backend.auth import require_role
from backend.services.admin import get_platform_stats, get_account_usage

router = APIRouter()


@router.get("/users", response_model=list[AdminUserResponse])
async def list_all_users(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role(UserRole.ADMIN))],
):
    result = await db.execute(select(User).options(selectinload(User.account)))
    return result.scalars().all()


@router.patch("/users/{user_id}", response_model=UserPrivate)
async def admin_update_user(
    user_id: uuid.UUID,
    user_update: AdminUserUpdate,
    _: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)
    return user


@router.get("/accounts", response_model=list[AdminAccountResponse])
async def list_all_accounts(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role(UserRole.ADMIN))],
):
    result = await db.execute(
        select(Account)
        .options(selectinload(Account.users))
        .options(selectinload(Account.companies))
        .options(selectinload(Account.subscription))
    )
    return result.scalars().all()


@router.patch("/accounts/{account_id}/subscription", response_model=SubscriptionResponse)
async def admin_update_subscription(
    account_id: uuid.UUID,
    subscription_update: SubscriptionUpdate,
    _: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Subscription).where(Subscription.account_id == account_id)
    )
    subscription = result.scalars().first()
    if not subscription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")

    update_data = subscription_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(subscription, field, value)

    await db.commit()
    await db.refresh(subscription)
    return subscription


@router.get("/companies", response_model=list[AdminCompanyResponse])
async def list_all_companies(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role(UserRole.ADMIN))],
):
    result = await db.execute(select(Company))
    return result.scalars().all()


@router.get("/executives", response_model=list[AdminExecutiveResponse])
async def list_all_executives(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role(UserRole.ADMIN))],
):
    result = await db.execute(select(Executive).options(selectinload(Executive.company)))
    return result.scalars().all()


@router.get("/stats", response_model=AdminStats)
async def platform_stats(
    _: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await get_platform_stats(db)


@router.get("/usage", response_model=list[AccountUsage])
async def account_usage(
    _: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await get_account_usage(db)
