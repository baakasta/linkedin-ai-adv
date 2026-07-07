from typing import Annotated
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from backend.db.db import get_db
from backend.models.user import Account
from backend.schemas.userschema import AccountResponse , AccountUpdate
from backend.schemas.subscriptionschema import SubscriptionResponse
from backend.models.subscription import Subscription

router = APIRouter()

@router.get("")
async def get_all_accounts(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(Account).options(selectinload(Account.users ) ).options(selectinload(Account.companies)).options(selectinload(Account.subscription)))
    accounts = result.scalars().all()
    return accounts


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(account_id: uuid.UUID, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(Account).options(selectinload(Account.users), selectinload(Account.companies), selectinload(Account.subscription)).where(Account.id == account_id),
    )
    account = result.scalars().first()
    if account:
        return account
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

@router.get("/{account_id}/subscription", response_model=SubscriptionResponse)
async def get_subscription(account_id: uuid.UUID, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(Subscription).where(Subscription.account_id == account_id)
    )
    subscription = result.scalars().first()
    if not subscription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    return subscription

@router.patch("/{account_id}", response_model=AccountResponse)
async def partial_update_account(
    account_id: uuid.UUID,
    account_update: AccountUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalars().first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )

    if account_update.name is not None:
        account.name = account_update.name

    await db.commit()
    result = await db.execute(
        select(Account)
        .options(selectinload(Account.users))
        .options(selectinload(Account.companies))
        .options(selectinload(Account.subscription))
        .where(Account.id == account_id)
    )
    return result.scalars().first()