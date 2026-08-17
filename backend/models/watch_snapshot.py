import uuid
from datetime import date
from sqlalchemy import UUID, ForeignKey, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from backend.db.db import Base, UUIDPrimaryKeyMixin, TimestampMixin


class WatchSnapshot(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "watch_snapshots"

    watch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("watches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    audit_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("audits.id", ondelete="SET NULL"),
        nullable=True,
    )
    period: Mapped[date] = mapped_column(Date, nullable=False)

    # extracted metrics from the audit
    metrics: Mapped[dict] = mapped_column(JSONB, nullable=False)

    watch: Mapped["Watch"] = relationship(back_populates="snapshots")
