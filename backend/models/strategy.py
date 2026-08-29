import uuid
from sqlalchemy import UUID, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.db.db import Base, UUIDPrimaryKeyMixin, TimestampMixin


class Strategy(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "strategies"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # optional audit this strategy is derived from
    audit_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("audits.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # full AI output (themes, axes, frequency, target, content mix)
    resultat: Mapped[dict] = mapped_column(JSONB, nullable=False)

    company: Mapped["Company"] = relationship(back_populates="strategies")
    audit: Mapped["Audit | None"] = relationship()
