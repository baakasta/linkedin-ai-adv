from typing import Annotated
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from backend.db.db import get_db
from backend.models.executive import Executive
from backend.models.company import Company
from backend.schemas.executiveschema import ExecutiveCreate, ExecutiveResponse,ExecutiveUpdate

router = APIRouter()

@router.get("", response_model=list[ExecutiveResponse])
async def get_all_executives(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(Executive).options(selectinload(Executive.company)))
    return result.scalars().all()

@router.get("/{executive_id}", response_model=ExecutiveResponse)
async def get_executive(executive_id: uuid.UUID, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(Executive).options(selectinload(Executive.company)).where(Executive.id == executive_id)
    )
    executive = result.scalars().first()
    if not executive:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Executive not found")
    return executive

@router.post("/create", response_model=ExecutiveResponse, status_code=status.HTTP_201_CREATED)
async def create_executive(executive: ExecutiveCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    # verify the company exists first
    company = (await db.execute(
        select(Company).where(Company.id == executive.company_id)
    )).scalars().first()
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

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
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(Executive).where(Executive.id == executive_id))
    executive = result.scalars().first()
    if not executive:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Executive not found",
        )

    update_data = executive_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(executive, field, value)

    await db.commit()
    await db.refresh(executive, attribute_names=["company"])
    return executive

@router.delete("/{executive_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_executive(executive_id: uuid.UUID, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(Executive).where(Executive.id == executive_id))
    executive = result.scalars().first()
    if not executive:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="executive not found",
        )

    await db.delete(executive)
    await db.commit()