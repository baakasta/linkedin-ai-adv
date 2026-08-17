import uuid
from sqlalchemy import UUID, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from backend.db.db import Base, UUIDPrimaryKeyMixin, TimestampMixin


class Watch(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "watches"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # competitor company IDs (will be LinkedIn URLs when extraction is built)
    competitor_ids: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # daily only for now
    frequency: Mapped[str] = mapped_column(String(20), nullable=False, default="daily")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")

    company: Mapped["Company"] = relationship(back_populates="watches")
    snapshots: Mapped[list["WatchSnapshot"]] = relationship(
        back_populates="watch", cascade="all, delete-orphan"
    )
    alerts: Mapped[list["WatchAlert"]] = relationship(
        back_populates="watch", cascade="all, delete-orphan"
    )
