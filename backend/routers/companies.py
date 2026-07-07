from typing import Annotated
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from backend.models.company import Company
from backend.db.db import get_db
from backend.schemas.companyschema import CompanyCreate, CompanyResponse,CompanyUpdate

router = APIRouter()

@router.get("", response_model=list[CompanyResponse])
async def get_all_companies(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(Company))
    return result.scalars().all()

@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(company_id: uuid.UUID, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(Company).options(selectinload(Company.account)).options(selectinload(Company.executives)).where(Company.id == company_id)
    )
    company = result.scalars().first()
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return company

@router.post("/create", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
async def create_company(company: CompanyCreate, account_id: uuid.UUID, db: Annotated[AsyncSession, Depends(get_db)]):
    existing = (await db.execute(
        select(Company).where(Company.name == company.name)
    )).scalars().first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Company name already exists")
    
    new_company = Company(
        account_id=account_id,
        name=company.name,
        linkedin_url=company.linkedin_url,
    )
    db.add(new_company)
    await db.commit()
    result = await db.execute(
        select(Company)
        .options(selectinload(Company.account))
        .options(selectinload(Company.executives))
        .where(Company.id == new_company.id)
    )
    return result.scalars().first()

@router.patch("/{company_id}", response_model=CompanyResponse)
async def partial_update_company(
    company_id: uuid.UUID,
    company_update: CompanyUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalars().first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    update_data = company_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(company, field, value)

    await db.commit()
    await db.refresh(company, attribute_names=["executives","account"])
    return company

@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(company_id: uuid.UUID, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalars().first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="company not found",
        )

    await db.delete(company)
    await db.commit()