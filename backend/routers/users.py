from typing import Annotated
from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func,select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from backend.models.user import User,Account
from backend.db.db import get_db
from backend.schemas.userschema import UserCreate, Token, UserUpdate, UserPrivate, UserPublic
from backend.models.subscription import Subscription, PlanTier, SubscriptionStatus
from backend.auth import (
    create_access_token,
    hash_password,
    oauth2_scheme,
    verify_access_token,
    verify_password,
    get_current_user,
)
from backend.config import settings

router = APIRouter()

@router.get("")
async def get_all_users(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(User).options(selectinload(User.account)))
    users = result.scalars().all()
    return users

@router.post(
    "/create",
    response_model=UserPrivate,
    status_code=status.HTTP_201_CREATED,
)
async def create_user(user: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]):

    existing_email = (await db.execute(select(User).where(func.lower(User.email) == user.email.lower()))).scalars().first()

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
        email=user.email.lower(),
        account_id=new_account.id, 
        password_hash=hash_password(user.password),  
    )
    db.add(new_user)
    await db.commit()
    
    result = await db.execute(
        select(User)
        .options(selectinload(User.account))
        .where(User.id == new_user.id)
    )
    return result.scalars().first()

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # Look up user by email (case-insensitive)
    # Note: OAuth2PasswordRequestForm uses "username" field, but we treat it as email
    result = await db.execute(
        select(User).where(
            func.lower(User.email) == form_data.username.lower(),
        ),
    )
    user = result.scalars().first()

    # Verify user exists and password is correct
    # Don't reveal which one failed (security best practice)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token with user id as subject
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires,
    )
    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserPrivate)
async def get_me(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get the currently authenticated user."""
    user_id = verify_access_token(token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Validate user_id is a valid integer (defense against malformed JWT)
    try:
        user_id_uuid = uuid.UUID(user_id)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(
        select(User).where(User.id == user_id_uuid),
    )
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

@router.patch("/me", response_model=UserPrivate)
async def update_me(
    user_update: UserUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if user_update.email is not None and user_update.email.lower() != current_user.email.lower():
        existing = (await db.execute(
            select(User).where(func.lower(User.email) == user_update.email.lower())
        )).scalars().first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    update_data = user_update.model_dump(exclude_unset=True)
    if "email" in update_data and update_data["email"] is not None:
        update_data["email"] = update_data["email"].lower()
    for field, value in update_data.items():
        setattr(current_user, field, value)

    await db.commit()
    await db.refresh(current_user)
    return current_user

@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_me(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await db.delete(current_user)
    await db.commit()

@router.get("/{user_id}", response_model=UserPublic)
async def get_user(user_id: uuid.UUID, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(User).options(selectinload(User.account)).where(User.id == user_id),
    )
    user = result.scalars().first()
    if user:
        return user
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

