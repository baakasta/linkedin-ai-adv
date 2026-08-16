import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, String, UUID
from sqlalchemy.orm import Mapped, mapped_column
from backend.db.db import Base, UUIDPrimaryKeyMixin, TimestampMixin


class ReportShare(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "report_shares"

    token: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    # audit | benchmark | monthly
    scope: Mapped[str] = mapped_column(String(20), nullable=False)

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    audit_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    benchmark_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    month: Mapped[str | None] = mapped_column(String(7), nullable=True)  # YYYY-MM

    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
