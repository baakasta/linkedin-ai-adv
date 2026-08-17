from typing import Annotated
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.db import get_db
from backend.models.user import User
from backend.models.company import Company
from backend.auth import get_current_user
from backend.schemas.dashboardschema import DashboardResponse
from backend.services.dashboard import build_dashboard

router = APIRouter()


@router.get("/companies/{company_id}/dashboard", response_model=DashboardResponse)
async def get_company_dashboard(
    company_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    company = (await db.execute(
        select(Company).where(Company.id == company_id)
    )).scalars().first()
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    if company.account_id != current_user.account_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your company")

    return await build_dashboard(db, company_id)
