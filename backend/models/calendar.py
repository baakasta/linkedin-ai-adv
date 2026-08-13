import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, String, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.db import Base, UUIDPrimaryKeyMixin, TimestampMixin
from backend.models.generation import Generation


class Calendar(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "calendars"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # cadence entre deux publications : 30, 60 ou 90 jours
    frequence: Mapped[int] = mapped_column(nullable=False, default=30)

    company: Mapped["Company"] = relationship(back_populates="calendar")
    slots: Mapped[list["CalendarSlot"]] = relationship(
        back_populates="calendar", cascade="all, delete-orphan"
    )


class CalendarSlot(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "calendar_slots"

    calendar_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("calendars.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    type_contenu: Mapped[str] = mapped_column(String(100), nullable=False)

    # remplis lors de la generation du contenu
    sujet: Mapped[str | None] = mapped_column(String(500), nullable=True)
    objectif: Mapped[str | None] = mapped_column(String(500), nullable=True)
    cta: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # planifie | genere | publie | annule
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="planifie")
    generation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("generations.id", ondelete="SET NULL"),
        nullable=True,
    )

    calendar: Mapped["Calendar"] = relationship(back_populates="slots")
    generation: Mapped["Generation | None"] = relationship()
