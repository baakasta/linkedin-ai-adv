from typing import Annotated
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from backend.db.db import get_db
from backend.models.user import Account, User
from backend.models.subscription import Subscription
from backend.schemas.userschema import AccountResponse, AccountUpdate
from backend.schemas.subscriptionschema import SubscriptionResponse
from backend.auth import get_current_user

router = APIRouter()

# get MY account — from token
@router.get("/me", response_model=AccountResponse)
async def get_my_account(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Account)
        .options(selectinload(Account.users))
        .options(selectinload(Account.companies))
        .options(selectinload(Account.subscription))
        .where(Account.id == current_user.account_id)
    )
    account = result.scalars().first()
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return account

# get MY subscription — from token
@router.get("/me/subscription", response_model=SubscriptionResponse)
async def get_my_subscription(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Subscription).where(Subscription.account_id == current_user.account_id)
    )
    subscription = result.scalars().first()
    if not subscription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    return subscription

# update MY account — from token
@router.patch("/me", response_model=AccountResponse)
async def update_my_account(
    account_update: AccountUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(Account).where(Account.id == current_user.account_id))
    account = result.scalars().first()
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

    if account_update.name is not None:
        account.name = account_update.name

    await db.commit()
    result = await db.execute(
        select(Account)
        .options(selectinload(Account.users))
        .options(selectinload(Account.companies))
        .options(selectinload(Account.subscription))
        .where(Account.id == current_user.account_id)
    )
    return result.scalars().first()
