from typing import Annotated
import uuid
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.db.db import get_db
from backend.models.user import User
from backend.models.company import Company
from backend.models.watch import Watch
from backend.models.watch_snapshot import WatchSnapshot
from backend.models.watch_alert import WatchAlert
from backend.models.audit import Audit
from backend.auth import get_current_user
from backend.schemas.watchschema import (
    WatchCreate,
    WatchUpdate,
    WatchResponse,
    WatchSnapshotResponse,
    WatchAlertResponse,
    VeilleOverview,
)
from backend.services.veille import create_snapshot_from_audit, build_veille_overview

router = APIRouter()


# --- Watch CRUD ---

@router.post("/watches", response_model=WatchResponse, status_code=status.HTTP_201_CREATED)
async def create_watch(
    payload: WatchCreate,
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

    watch = Watch(
        company_id=payload.company_id,
        competitor_ids=[str(c) for c in payload.competitor_ids] if payload.competitor_ids else [],
    )
    db.add(watch)
    await db.commit()
    await db.refresh(watch)

    watch.latest_snapshot = None
    return watch


@router.get("/watches/{watch_id}", response_model=WatchResponse)
async def get_watch(
    watch_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    watch = (await db.execute(
        select(Watch)
        .options(
            selectinload(Watch.company),
            selectinload(Watch.snapshots),
        )
        .where(Watch.id == watch_id)
    )).scalars().first()
    if not watch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watch not found")
    if watch.company.account_id != current_user.account_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your watch")

    sorted_snapshots = sorted(watch.snapshots, key=lambda s: s.created_at, reverse=True)
    latest = sorted_snapshots[0] if sorted_snapshots else None

    return WatchResponse(
        id=watch.id,
        company_id=watch.company_id,
        competitor_ids=watch.competitor_ids,
        frequency=watch.frequency,
        status=watch.status,
        latest_snapshot=WatchSnapshotResponse.model_validate(latest) if latest else None,
        created_at=watch.created_at,
    )


@router.patch("/watches/{watch_id}", response_model=WatchResponse)
async def update_watch(
    watch_id: uuid.UUID,
    payload: WatchUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    watch = (await db.execute(
        select(Watch)
        .options(selectinload(Watch.company), selectinload(Watch.snapshots))
        .where(Watch.id == watch_id)
    )).scalars().first()
    if not watch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watch not found")
    if watch.company.account_id != current_user.account_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your watch")

    if payload.competitor_ids is not None:
        watch.competitor_ids = [str(c) for c in payload.competitor_ids]
    if payload.status is not None:
        watch.status = payload.status.value

    await db.commit()
    await db.refresh(watch)

    sorted_snapshots = sorted(watch.snapshots, key=lambda s: s.created_at, reverse=True)
    latest = sorted_snapshots[0] if sorted_snapshots else None

    return WatchResponse(
        id=watch.id,
        company_id=watch.company_id,
        competitor_ids=watch.competitor_ids,
        frequency=watch.frequency,
        status=watch.status,
        latest_snapshot=WatchSnapshotResponse.model_validate(latest) if latest else None,
        created_at=watch.created_at,
    )


@router.delete("/watches/{watch_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_watch(
    watch_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    watch = (await db.execute(
        select(Watch)
        .options(selectinload(Watch.company))
        .where(Watch.id == watch_id)
    )).scalars().first()
    if not watch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watch not found")
    if watch.company.account_id != current_user.account_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your watch")

    await db.delete(watch)
    await db.commit()


# --- Snapshots ---

@router.post(
    "/watches/{watch_id}/snapshots",
    response_model=WatchSnapshotResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_snapshot(
    watch_id: uuid.UUID,
    audit_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a snapshot from an existing audit (audit-based monitoring)."""
    watch = (await db.execute(
        select(Watch).options(selectinload(Watch.company)).where(Watch.id == watch_id)
    )).scalars().first()
    if not watch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watch not found")
    if watch.company.account_id != current_user.account_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your watch")

    audit = (await db.execute(
        select(Audit).where(Audit.id == audit_id)
    )).scalars().first()
    if not audit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit not found")
    if audit.company_id != watch.company_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Audit does not belong to this watch's company",
        )

    snapshot = await create_snapshot_from_audit(db, watch_id, audit)
    await db.commit()
    await db.refresh(snapshot)
    return snapshot


@router.get("/watches/{watch_id}/snapshots", response_model=list[WatchSnapshotResponse])
async def list_snapshots(
    watch_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    watch = (await db.execute(
        select(Watch).options(selectinload(Watch.company)).where(Watch.id == watch_id)
    )).scalars().first()
    if not watch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watch not found")
    if watch.company.account_id != current_user.account_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your watch")

    snapshots = (await db.execute(
        select(WatchSnapshot)
        .where(WatchSnapshot.watch_id == watch_id)
        .order_by(WatchSnapshot.period)
    )).scalars().all()
    return snapshots


# --- Alerts ---

@router.get("/watches/{watch_id}/alerts", response_model=list[WatchAlertResponse])
async def list_alerts(
    watch_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    watch = (await db.execute(
        select(Watch).options(selectinload(Watch.company)).where(Watch.id == watch_id)
    )).scalars().first()
    if not watch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watch not found")
    if watch.company.account_id != current_user.account_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your watch")

    alerts = (await db.execute(
        select(WatchAlert)
        .where(WatchAlert.watch_id == watch_id)
        .order_by(desc(WatchAlert.created_at))
    )).scalars().all()
    return alerts


@router.patch("/watches/{watch_id}/alerts/{alert_id}", response_model=WatchAlertResponse)
async def mark_alert_read(
    watch_id: uuid.UUID,
    alert_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    watch = (await db.execute(
        select(Watch).options(selectinload(Watch.company)).where(Watch.id == watch_id)
    )).scalars().first()
    if not watch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watch not found")
    if watch.company.account_id != current_user.account_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your watch")

    alert = (await db.execute(
        select(WatchAlert).where(WatchAlert.id == alert_id, WatchAlert.watch_id == watch_id)
    )).scalars().first()
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    alert.read = True
    await db.commit()
    await db.refresh(alert)
    return alert


# --- Veille Overview ---

@router.get("/watches/{watch_id}/overview", response_model=VeilleOverview)
async def get_veille_overview(
    watch_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    watch = (await db.execute(
        select(Watch).options(selectinload(Watch.company)).where(Watch.id == watch_id)
    )).scalars().first()
    if not watch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watch not found")
    if watch.company.account_id != current_user.account_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your watch")

    overview = await build_veille_overview(db, watch_id)

    return VeilleOverview(
        watch_id=overview["watch_id"],
        company_id=overview["company_id"],
        latest_snapshot=WatchSnapshotResponse.model_validate(overview["latest_snapshot"]) if overview["latest_snapshot"] else None,
        competitor_snapshots=overview["competitor_snapshots"],
        recent_alerts=[WatchAlertResponse.model_validate(a) for a in overview["recent_alerts"]],
        ai_analysis=overview["ai_analysis"],
    )
