from datetime import date, timedelta
from typing import Annotated
import asyncio
import uuid

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.dependencies import require_plan
from backend.models.subscription import PlanTier
from backend.config import settings
from backend.db.db import AsyncSessionLocal, get_db
from backend.models.audit import Audit
from backend.models.calendar import Calendar, CalendarSlot
from backend.models.company import Company
from backend.models.generation import Generation
from backend.models.user import User
from backend.schemas.calendarschema import (
    CalendarCreate,
    CalendarResponse,
    CalendarSlotResponse,
    CalendarUpdate,
)

router = APIRouter()

DEP_PRO = require_plan(PlanTier.PRO)

HORIZON_JOURS = 90

TYPES_CONTENU = [
    "publication",
    "carrousel",
    "idee_video",
    "temoignage_client",
    "etude_de_cas",
    "actualite",
    "publication_rh",
    "publication_dirigeant",
    "annonce_recrutement",
]


def _type_au_index(index: int) -> str:
    return TYPES_CONTENU[index % len(TYPES_CONTENU)]


async def _verifier_company(
    db: AsyncSession, company_id: uuid.UUID, current_user: User
) -> Company:
    company = (await db.execute(
        select(Company).where(Company.id == company_id)
    )).scalars().first()
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    if company.account_id != current_user.account_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your company")
    return company


def _generer_slots(calendar: Calendar, ancrage: date) -> list[CalendarSlot]:
    slots: list[CalendarSlot] = []
    jour = ancrage
    index = 0
    limite = ancrage + timedelta(days=HORIZON_JOURS)
    while jour <= limite:
        slots.append(CalendarSlot(
            calendar_id=calendar.id,
            date=jour,
            type_contenu=_type_au_index(index),
            status="planifie",
        ))
        index += 1
        jour += timedelta(days=calendar.frequence)
    return slots


async def _charger_calendar(db: AsyncSession, company_id: uuid.UUID) -> Calendar | None:
    db.expire_all()
    calendar = (await db.execute(
        select(Calendar)
        .options(selectinload(Calendar.slots))
        .where(Calendar.company_id == company_id)
    )).scalars().first()
    if calendar:
        calendar.slots.sort(key=lambda s: s.date)
    return calendar


async def _contexte_entreprise_company(db: AsyncSession, company_id: uuid.UUID) -> dict:
    audit = (await db.execute(
        select(Audit)
        .where(Audit.company_id == company_id)
        .order_by(Audit.created_at.desc())
    )).scalars().first()
    ent = {}
    if audit:
        ent = (audit.linkedin_data or {}).get("entreprise") or {}
    return {
        "nom": ent.get("nom") or "",
        "secteur": ent.get("secteur") or "",
        "cibleClient": "",
        "services": ent.get("services") or [],
        "positionnement": ent.get("description") or ent.get("slogan") or "",
        "tonSouhaite": "",
    }


async def _generer_contenu_slot(db: AsyncSession, slot: CalendarSlot) -> None:
    company = (await db.execute(
        select(Company).where(Company.id == slot.calendar.company_id)
    )).scalars().first()
    contexte = await _contexte_entreprise_company(db, slot.calendar.company_id)
    if not contexte["nom"]:
        contexte["nom"] = company.name if company else str(slot.calendar.company_id)
    ai_payload = {
        "type_contenu": slot.type_contenu,
        "brief": {
            "type_contenu": slot.type_contenu,
            "contexte": f"contenu programme dans le calendrier editorial de {contexte['nom']}",
        },
        "contexte_entreprise": contexte,
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{settings.ai_service_url}/api/generations",
                json=ai_payload,
                timeout=60.0,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"AI service error: {str(exc)}",
            )

    ai_result = response.json()
    variantes = ai_result.get("variantes", [])
    if not variantes:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI service returned no variants",
        )

    premiere = variantes[0]
    contenu = str(premiere.get("contenu", "") or "").strip()
    slot.sujet = contenu[:500] or None
    slot.objectif = str(premiere.get("angle", "") or "").strip()[:500] or None
    slot.cta = str(premiere.get("cta", "") or "").strip()[:500] or None
    slot.status = "genere"

    generation = Generation(
        company_id=company.id,
        type_contenu=slot.type_contenu,
        brief=ai_payload["brief"],
        titre_interne=ai_result.get("titre_interne"),
        variantes={"variantes": variantes},
        marqueurs_a_completer=ai_result.get(
            "marqueurs_a_completer",
            ai_result.get("marqueurs_acompleter", []),
        ),
    )
    db.add(generation)
    await db.flush()
    slot.generation_id = generation.id


async def _generer_contenu_slots(slots: list[CalendarSlot]) -> tuple[int, int]:
    async def traiter(slot: CalendarSlot) -> bool:
        async with AsyncSessionLocal() as session:
            charge = (await session.execute(
                select(CalendarSlot)
                .options(selectinload(CalendarSlot.calendar))
                .where(CalendarSlot.id == slot.id)
            )).scalars().first()
            if not charge:
                return False
            try:
                await _generer_contenu_slot(session, charge)
                await session.commit()
                return True
            except HTTPException:
                await session.rollback()
                return False

    resultats = await asyncio.gather(*(traiter(s) for s in slots))
    ok = sum(1 for r in resultats if r)
    return ok, len(slots) - ok


# --- Calendriers ---

@router.post("", response_model=CalendarResponse, status_code=status.HTTP_201_CREATED)
async def create_calendar(
    payload: CalendarCreate,
    current_user: Annotated[User, Depends(DEP_PRO)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await _verifier_company(db, payload.company_id, current_user)

    existing = (await db.execute(
        select(Calendar).where(Calendar.company_id == payload.company_id)
    )).scalars().first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Calendar already exists for this company",
        )

    calendar = Calendar(company_id=payload.company_id, frequence=payload.frequence.value)
    db.add(calendar)
    await db.flush()

    slots = _generer_slots(calendar, date.today())
    for slot in slots:
        db.add(slot)

    await db.commit()

    generes, erreurs = await _generer_contenu_slots(slots)

    calendar = await _charger_calendar(db, payload.company_id)
    return calendar


@router.get("/company/{company_id}", response_model=CalendarResponse)
async def get_company_calendar(
    company_id: uuid.UUID,
    current_user: Annotated[User, Depends(DEP_PRO)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await _verifier_company(db, company_id, current_user)
    calendar = await _charger_calendar(db, company_id)
    if not calendar:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No calendar for this company")
    return calendar


@router.patch("/company/{company_id}", response_model=CalendarResponse)
async def update_calendar_frequence(
    company_id: uuid.UUID,
    payload: CalendarUpdate,
    current_user: Annotated[User, Depends(DEP_PRO)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await _verifier_company(db, company_id, current_user)
    calendar = await _charger_calendar(db, company_id)
    if not calendar:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No calendar for this company")

    if payload.frequence.value != calendar.frequence:
        gardes = [s for s in calendar.slots if s.status in ("genere", "publie")]
        calendar.slots = gardes

        calendar.frequence = payload.frequence.value

        if gardes:
            ancrage = max(s.date for s in gardes)
            jour = ancrage + timedelta(days=calendar.frequence)
            index = len(gardes)
        else:
            ancrage = date.today()
            jour = ancrage
            index = 0

        limite = ancrage + timedelta(days=HORIZON_JOURS)
        while jour <= limite:
            calendar.slots.append(CalendarSlot(
                date=jour,
                type_contenu=_type_au_index(index),
                status="planifie",
            ))
            index += 1
            jour += timedelta(days=calendar.frequence)

    await db.commit()

    nouveaux = [s for s in calendar.slots if s.status == "planifie"]
    if nouveaux:
        await _generer_contenu_slots(nouveaux)

    calendar = await _charger_calendar(db, company_id)
    return calendar


# --- Slots ---

@router.post("/slots/{slot_id}/generate", response_model=CalendarSlotResponse)
async def generate_slot_content(
    slot_id: uuid.UUID,
    current_user: Annotated[User, Depends(DEP_PRO)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    slot = (await db.execute(
        select(CalendarSlot)
        .options(selectinload(CalendarSlot.calendar).selectinload(Calendar.company))
        .where(CalendarSlot.id == slot_id)
    )).scalars().first()
    if not slot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Slot not found")
    if slot.calendar.company.account_id != current_user.account_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your slot")

    await _generer_contenu_slot(db, slot)
    await db.commit()
    await db.refresh(slot)
    return slot


@router.delete("/slots/{slot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_slot(
    slot_id: uuid.UUID,
    current_user: Annotated[User, Depends(DEP_PRO)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    slot = (await db.execute(
        select(CalendarSlot)
        .options(selectinload(CalendarSlot.calendar).selectinload(Calendar.company))
        .where(CalendarSlot.id == slot_id)
    )).scalars().first()
    if not slot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Slot not found")
    if slot.calendar.company.account_id != current_user.account_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your slot")

    await db.delete(slot)
    await db.commit()
