from typing import Annotated
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.db.db import get_db
from backend.models.user import User
from backend.models.company import Company
from backend.models.audit import Audit
from backend.models.strategy import Strategy
from backend.auth import get_current_user
from backend.schemas.strategyschema import StrategyCreate, StrategyResponse
from backend.services.ai_client import call_ai_or_placeholder
from backend.services.strategy import build_strategy_placeholder
from backend.services.quotas import enforce_ai_quota

router = APIRouter()


async def _get_owned_company(company_id: uuid.UUID, current_user: User, db: AsyncSession) -> Company:
    company = (await db.execute(
        select(Company).where(Company.id == company_id)
    )).scalars().first()
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    if company.account_id != current_user.account_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your company")
    return company


@router.post("/strategies", response_model=StrategyResponse, status_code=status.HTTP_201_CREATED)
async def create_strategy(
    payload: StrategyCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    company = await _get_owned_company(payload.company_id, current_user, db)

    await enforce_ai_quota(db, current_user, "strategies")

    score_global = None
    ai_payload = {
        "company_id": str(company.id),
        "company_name": company.name,
        "linkedin_url": company.linkedin_url,
        "audit_id": str(payload.audit_id) if payload.audit_id else None,
        "contexte_entreprise": {"name": company.name, "linkedin_url": company.linkedin_url},
    }

    if payload.audit_id:
        audit = (await db.execute(
            select(Audit).where(Audit.id == payload.audit_id)
        )).scalars().first()
        if not audit:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit not found")
        if audit.company_id != company.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Audit does not belong to this company")
        score_global = audit.score_global
        ai_payload["contexte_entreprise"]["analyse_ia"] = audit.analyse_ia

    placeholder = build_strategy_placeholder(company.name, score_global)
    ai_result = await call_ai_or_placeholder("/api/strategies", ai_payload, placeholder)

    strategy = Strategy(
        company_id=company.id,
        audit_id=payload.audit_id,
        resultat=ai_result if isinstance(ai_result, dict) else {"data": ai_result},
    )
    db.add(strategy)
    await db.commit()
    await db.refresh(strategy)
    return strategy


@router.get("/strategies/{strategy_id}", response_model=StrategyResponse)
async def get_strategy(
    strategy_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    strategy = (await db.execute(
        select(Strategy)
        .options(selectinload(Strategy.company))
        .where(Strategy.id == strategy_id)
    )).scalars().first()
    if not strategy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Strategy not found")
    if strategy.company.account_id != current_user.account_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your strategy")
    return strategy


@router.get("/strategies/company/{company_id}", response_model=list[StrategyResponse])
async def get_company_strategies(
    company_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await _get_owned_company(company_id, current_user, db)
    result = await db.execute(
        select(Strategy)
        .where(Strategy.company_id == company_id)
        .order_by(Strategy.created_at.desc())
    )
    return result.scalars().all()