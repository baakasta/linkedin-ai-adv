from typing import Annotated
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from backend.db.db import get_db
from backend.models.executive import Executive
from backend.models.company import Company
from backend.models.user import User, UserRole
from backend.schemas.executiveschema import ExecutiveCreate, ExecutiveResponse, ExecutiveUpdate
from backend.auth import get_current_user

router = APIRouter()

@router.get("/{executive_id}", response_model=ExecutiveResponse)
async def get_executive(
    executive_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    result = await db.execute(
        select(Executive)
        .options(selectinload(Executive.company))
        .where(Executive.id == executive_id)
    )
    executive = result.scalars().first()
    if not executive:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Executive not found")

    if executive.company.account_id != current_user.account_id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your executive")

    return executive

@router.post("/create", response_model=ExecutiveResponse, status_code=status.HTTP_201_CREATED)
async def create_executive(
    executive: ExecutiveCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    company = (await db.execute(
        select(Company).where(Company.id == executive.company_id)
    )).scalars().first()
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

    # ownership check — company must belong to current user's account
    if company.account_id != current_user.account_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your company")

    new_executive = Executive(
        company_id=executive.company_id,
        full_name=executive.full_name,
        job_title=executive.job_title,
        linkedin_url=executive.linkedin_url,
    )
    db.add(new_executive)
    await db.commit()
    result = await db.execute(
        select(Executive)
        .options(selectinload(Executive.company))
        .where(Executive.id == new_executive.id)
    )
    return result.scalars().first()

@router.patch("/{executive_id}", response_model=ExecutiveResponse)
async def partial_update_executive(
    executive_id: uuid.UUID,
    executive_update: ExecutiveUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Executive)
        .options(selectinload(Executive.company))
        .where(Executive.id == executive_id)
    )
    executive = result.scalars().first()
    if not executive:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Executive not found")

    # ownership check via company
    if executive.company.account_id != current_user.account_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your executive")

    update_data = executive_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(executive, field, value)

    await db.commit()
    result = await db.execute(
        select(Executive)
        .options(selectinload(Executive.company))
        .where(Executive.id == executive_id)
    )
    return result.scalars().first()

@router.delete("/{executive_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_executive(
    executive_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Executive)
        .options(selectinload(Executive.company))
        .where(Executive.id == executive_id)
    )
    executive = result.scalars().first()
    if not executive:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Executive not found")

    # ownership check via company
    if executive.company.account_id != current_user.account_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your executive")

    await db.delete(executive)
    await db.commit()