import asyncio
import logging
from datetime import date, timedelta

from sqlalchemy import select

from backend.config import settings
from backend.db.db import AsyncSessionLocal
from backend.models.calendar import CalendarSlot
from backend.routers.calendar import _generer_contenu_slots

logger = logging.getLogger("uvicorn.error")


async def _generer_slots_dues() -> tuple[int, int]:
    limite = date.today() + timedelta(days=settings.generation_lookahead_days)
    async with AsyncSessionLocal() as session:
        slots = (await session.execute(
            select(CalendarSlot)
            .where(
                CalendarSlot.status == "planifie",
                CalendarSlot.date <= limite,
            )
        )).scalars().all()
    if not slots:
        return 0, 0
    return await _generer_contenu_slots(slots)


async def generation_loop() -> None:
    interval = settings.scheduler_interval_hours * 3600
    logger.info(
        "Scheduler started (interval=%sh, lookahead=%sd)",
        settings.scheduler_interval_hours,
        settings.generation_lookahead_days,
    )
    while True:
        try:
            generes, erreurs = await _generer_slots_dues()
            if generes or erreurs:
                logger.info("Scheduled generation: %s generated, %s errors", generes, erreurs)
        except Exception:
            logger.exception("Scheduled generation failed")
        await asyncio.sleep(interval)
