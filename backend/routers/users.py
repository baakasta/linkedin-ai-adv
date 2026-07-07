from typing import Annotated
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from backend.models.user import User,Account
from backend.db.db import get_db
from backend.schemas.userschema import UserCreate, UserResponse, UserUpdate
from backend.models.subscription import Subscription, PlanTier, SubscriptionStatus

router = APIRouter()

@router.get("")
async def get_all_users(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(User).options(selectinload(User.account)))
    users = result.scalars().all()
    return users

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: uuid.UUID, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(User).options(selectinload(User.account)).where(User.id == user_id),
    )
    user = result.scalars().first()
    if user:
        return user
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

@router.post(
    "/create",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_user(user: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]):

    existing_email = (await db.execute(select(User).where(User.email == user.email))).scalars().first()

    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    new_account = Account(name=user.account_name)
    db.add(new_account)
    await db.flush()  # confirms new_account.id without committing yet

    new_subscription = Subscription(
    account_id=new_account.id,
    plan_tier=PlanTier.DECOUVERTE,
    status=SubscriptionStatus.ACTIVE,
    )
    db.add(new_subscription)

    new_user = User(
        full_name=user.full_name,
        email=user.email,
        account_id=new_account.id, 
    )
    db.add(new_user)
    await db.commit()
    
    result = await db.execute(
        select(User)
        .options(selectinload(User.account))
        .where(User.id == new_user.id)
    )
    return result.scalars().first()

@router.patch("/{user_id}", response_model=UserResponse)
async def partial_update_user(
    user_id: uuid.UUID,
    user_update: UserUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user_update.email is not None and user_update.email != user.email:
        result = await db.execute(
            select(User).where(User.email == user_update.email),
        )
        existing_email = result.scalars().first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user, attribute_names=["account"])
    return user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: uuid.UUID, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    await db.delete(user)
    await db.commit()
