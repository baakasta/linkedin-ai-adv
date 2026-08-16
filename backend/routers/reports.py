from typing import Annotated
from datetime import datetime, timedelta, timezone
import secrets
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
from backend.models.report_share import ReportShare
from backend.schemas.reportshareschema import (
    ReportHistory,
    ReportShareCreate,
    ReportShareResponse,
    ReportShareUrl,
    HistoryEntry,
)
from backend.auth import get_current_user, get_current_user_optional
from backend.services.reports import (
    audit_report_pdf,
    benchmark_report_pdf,
    monthly_report_pdf,
)

router = APIRouter()

SHARE_DEFAULT_DUREE_JOURS = 7


def _mois_key(dt: datetime) -> str:
    return f"{dt.year:04d}-{dt.month:02d}"


def _pdf_response(content: bytes, filename: str) -> Response:
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


async def _monthly_report_data(
    db: AsyncSession,
    company_id: uuid.UUID,
    month: str,
) -> tuple[dict, list, list, list, list]:
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

    return summary, audits, benchmarks, generations, optimizations


async def _verifier_share(db: AsyncSession, token: str) -> ReportShare:
    share = (await db.execute(
        select(ReportShare).where(ReportShare.token == token)
    )).scalars().first()
    if not share:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid share link")
    if share.revoked:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Share has been revoked")
    if share.expires_at and share.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Share link has expired")
    return share


async def _build_history(
    db: AsyncSession,
    company: Company,
    share_token: str | None = None,
) -> list[HistoryEntry]:
    reports: list[HistoryEntry] = []

    audits = (await db.execute(
        select(Audit)
        .where(Audit.company_id == company.id)
        .order_by(Audit.created_at.desc())
    )).scalars().all()
    for audit in audits:
        url = f"/api/reports/audit/{audit.id}"
        if share_token:
            url += f"?share={share_token}"
        reports.append(HistoryEntry(
            id=audit.id,
            type="audit",
            titre=f"Rapport d'audit — {company.name} — {audit.created_at:%d/%m/%Y}",
            created_at=audit.created_at,
            url=url,
        ))

    benchmarks = (await db.execute(
        select(Benchmark)
        .where(Benchmark.company_id == company.id)
        .order_by(Benchmark.created_at.desc())
    )).scalars().all()
    for benchmark in benchmarks:
        score = (benchmark.resultat or {}).get("score_benchmark")
        titre = f"Rapport de benchmark — {company.name} — {benchmark.created_at:%d/%m/%Y}"
        if score is not None:
            titre += f" (score {score}/100)"
        url = f"/api/reports/benchmark/{benchmark.id}"
        if share_token:
            url += f"?share={share_token}"
        reports.append(HistoryEntry(
            id=benchmark.id,
            type="benchmark",
            titre=titre,
            created_at=benchmark.created_at,
            url=url,
        ))

    mois: set[str] = set()
    for source in [*audits, *benchmarks]:
        mois.add(_mois_key(source.created_at))
    generations = (await db.execute(
        select(Generation.created_at).where(Generation.company_id == company.id)
    )).scalars().all()
    for created in generations:
        mois.add(_mois_key(created))
    optimizations = (await db.execute(
        select(Optimization.created_at)
        .join(Recommendation, Recommendation.id == Optimization.recommendation_id)
        .join(Audit, Audit.id == Recommendation.audit_id)
        .where(Audit.company_id == company.id)
    )).scalars().all()
    for created in optimizations:
        mois.add(_mois_key(created))

    for key in sorted(mois, reverse=True):
        annee, mois_num = (int(part) for part in key.split("-"))
        if mois_num == 12:
            fin = datetime(annee + 1, 1, 1, tzinfo=timezone.utc)
        else:
            fin = datetime(annee, mois_num + 1, 1, tzinfo=timezone.utc)
        url = f"/api/reports/monthly?company_id={company.id}&month={key}"
        if share_token:
            url += f"&share={share_token}"
        reports.append(HistoryEntry(
            type="monthly",
            titre=f"Synthèse mensuelle {key}",
            created_at=fin - timedelta(days=1),
            month=key,
            url=url,
        ))

    reports.sort(key=lambda r: r.created_at or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    return reports


def _autorise_par_share(share: ReportShare | None, company_id: uuid.UUID) -> bool:
    return share is not None and share.scope == "company" and share.company_id == company_id


@router.get("/reports/audit/{audit_id}", response_class=Response)
async def get_audit_report(
    audit_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    share: str | None = Query(default=None),
    current_user: Annotated[User | None, Depends(get_current_user_optional)] = None,
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

    valide = False
    if share:
        valide = _autorise_par_share(await _verifier_share(db, share), audit.company_id)
    elif current_user is not None and audit.company.account_id == current_user.account_id:
        valide = True
    if not valide:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your audit")

    recommendations = (await db.execute(
        select(Recommendation).where(Recommendation.audit_id == audit_id)
    )).scalars().all()

    pdf = audit_report_pdf(audit.company.name, audit, recommendations)
    return _pdf_response(pdf, f"audit_{audit_id}.pdf")


@router.get("/reports/benchmark/{benchmark_id}", response_class=Response)
async def get_benchmark_report(
    benchmark_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    share: str | None = Query(default=None),
    current_user: Annotated[User | None, Depends(get_current_user_optional)] = None,
):
    benchmark = (await db.execute(
        select(Benchmark)
        .options(selectinload(Benchmark.company))
        .where(Benchmark.id == benchmark_id)
    )).scalars().first()
    if not benchmark:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Benchmark not found")

    valide = False
    if share:
        valide = _autorise_par_share(await _verifier_share(db, share), benchmark.company_id)
    elif current_user is not None and benchmark.company.account_id == current_user.account_id:
        valide = True
    if not valide:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your benchmark")

    pdf = benchmark_report_pdf(benchmark.company.name, benchmark)
    return _pdf_response(pdf, f"benchmark_{benchmark_id}.pdf")


@router.get("/reports/monthly", response_class=Response)
async def get_monthly_report(
    company_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    month: str = Query(pattern=r"^\d{4}-(0[1-9]|1[0-2])$"),
    share: str | None = Query(default=None),
    current_user: Annotated[User | None, Depends(get_current_user_optional)] = None,
):
    company = (await db.execute(
        select(Company).where(Company.id == company_id)
    )).scalars().first()
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

    valide = False
    if share:
        valide = _autorise_par_share(await _verifier_share(db, share), company_id)
    elif current_user is not None and company.account_id == current_user.account_id:
        valide = True
    if not valide:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your company")

    summary, audits, benchmarks, generations, optimizations = await _monthly_report_data(
        db, company_id, month
    )

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


# --- Historique ---

@router.get("/reports/history", response_model=ReportHistory)
async def get_report_history(
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

    reports = await _build_history(db, company)
    return ReportHistory(reports=reports)


# --- Partage sécurisé ---

@router.post("/reports/share", response_model=ReportShareUrl, status_code=status.HTTP_201_CREATED)
async def create_report_share(
    payload: ReportShareCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    company = (await db.execute(
        select(Company).where(Company.id == payload.company_id)
    )).scalars().first()
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    if company.account_id != current_user.account_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your company")

    if payload.expires_at is not None:
        expires_at = datetime(
            payload.expires_at.year,
            payload.expires_at.month,
            payload.expires_at.day,
            23, 59, 59, 999999,
            tzinfo=timezone.utc,
        )
        if expires_at <= datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="expires_at must be in the future",
            )
    else:
        expires_at = datetime.now(timezone.utc) + timedelta(days=SHARE_DEFAULT_DUREE_JOURS)

    share = ReportShare(
        token=secrets.token_urlsafe(32),
        scope="company",
        company_id=company.id,
        expires_at=expires_at,
        revoked=False,
    )
    db.add(share)
    await db.commit()
    await db.refresh(share)

    return ReportShareUrl(
        token=share.token,
        url=f"/api/reports/shared/{share.token}",
        expires_at=share.expires_at,
    )


@router.get("/reports/shared/{token}", response_model=ReportHistory)
async def get_shared_report(
    token: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    share = await _verifier_share(db, token)
    company = (await db.execute(
        select(Company).where(Company.id == share.company_id)
    )).scalars().first()
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

    reports = await _build_history(db, company, share_token=token)
    return ReportHistory(reports=reports)


@router.delete("/reports/share/{token}", response_model=ReportShareResponse)
async def revoke_report_share(
    token: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    share = (await db.execute(
        select(ReportShare).where(ReportShare.token == token)
    )).scalars().first()
    if not share:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Share not found")
    company = (await db.execute(
        select(Company).where(Company.id == share.company_id)
    )).scalars().first()
    if not company or company.account_id != current_user.account_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your share")

    share.revoked = True
    await db.commit()
    await db.refresh(share)
    return share
