from typing import Annotated
from datetime import datetime, timezone
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.db.db import get_db
from backend.models.user import User
from backend.models.company import Company
from backend.models.audit import Audit
from backend.models.recommendation import Recommendation
from backend.models.optimization import Optimization
from backend.models.generation import Generation
from backend.models.benchmark import Benchmark
from backend.auth import get_current_user
from backend.services.reports import (
    audit_report_pdf,
    benchmark_report_pdf,
    monthly_report_pdf,
)

router = APIRouter()


def _pdf_response(content: bytes, filename: str) -> Response:
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/reports/audit/{audit_id}", response_class=Response)
async def get_audit_report(
    audit_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    audit = (await db.execute(
        select(Audit)
        .options(
            selectinload(Audit.company),
            selectinload(Audit.recommendations),
        )
        .where(Audit.id == audit_id)
    )).scalars().first()
    if not audit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit not found")
    if audit.company.account_id != current_user.account_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your audit")

    recommendations = (await db.execute(
        select(Recommendation).where(Recommendation.audit_id == audit_id)
    )).scalars().all()

    pdf = audit_report_pdf(audit.company.name, audit, recommendations)
    return _pdf_response(pdf, f"audit_{audit_id}.pdf")


@router.get("/reports/benchmark/{benchmark_id}", response_class=Response)
async def get_benchmark_report(
    benchmark_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    benchmark = (await db.execute(
        select(Benchmark)
        .options(selectinload(Benchmark.company))
        .where(Benchmark.id == benchmark_id)
    )).scalars().first()
    if not benchmark:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Benchmark not found")
    if benchmark.company.account_id != current_user.account_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your benchmark")

    pdf = benchmark_report_pdf(benchmark.company.name, benchmark)
    return _pdf_response(pdf, f"benchmark_{benchmark_id}.pdf")


@router.get("/reports/monthly", response_class=Response)
async def get_monthly_report(
    company_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    month: str = Query(pattern=r"^\d{4}-(0[1-9]|1[0-2])$"),
):
    company = (await db.execute(
        select(Company).where(Company.id == company_id)
    )).scalars().first()
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    if company.account_id != current_user.account_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your company")

    year, month_num = (int(part) for part in month.split("-"))
    start = datetime(year, month_num, 1, tzinfo=timezone.utc)
    if month_num == 12:
        end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        end = datetime(year, month_num + 1, 1, tzinfo=timezone.utc)

    audits = (await db.execute(
        select(Audit)
        .where(
            Audit.company_id == company_id,
            Audit.created_at >= start,
            Audit.created_at < end,
        )
        .order_by(Audit.created_at.desc())
    )).scalars().all()

    benchmarks = (await db.execute(
        select(Benchmark)
        .where(
            Benchmark.company_id == company_id,
            Benchmark.created_at >= start,
            Benchmark.created_at < end,
        )
        .order_by(Benchmark.created_at.desc())
    )).scalars().all()

    generations = (await db.execute(
        select(Generation)
        .where(
            Generation.company_id == company_id,
            Generation.created_at >= start,
            Generation.created_at < end,
        )
        .order_by(Generation.created_at.desc())
    )).scalars().all()

    optimizations = (await db.execute(
        select(Optimization)
        .join(Recommendation, Recommendation.id == Optimization.recommendation_id)
        .join(Audit, Audit.id == Recommendation.audit_id)
        .where(
            Audit.company_id == company_id,
            Optimization.created_at >= start,
            Optimization.created_at < end,
        )
        .order_by(Optimization.created_at.desc())
    )).scalars().all()

    summary = {
        "audits": len(audits),
        "benchmarks": len(benchmarks),
        "generations": len(generations),
        "optimizations": len(optimizations),
    }

    pdf = monthly_report_pdf(
        company.name,
        month,
        summary,
        audits,
        benchmarks,
        generations,
        optimizations,
    )
    return _pdf_response(pdf, f"synthèse_mensuelle_{month}.pdf")
