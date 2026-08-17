import uuid
from sqlalchemy import UUID, ForeignKey, String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.db.db import Base, UUIDPrimaryKeyMixin, TimestampMixin


class WatchAlert(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "watch_alerts"

    watch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("watches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="info")
    read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    watch: Mapped["Watch"] = relationship(back_populates="alerts")
