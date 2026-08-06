import uuid
from datetime import datetime
from sqlalchemy import UUID, ForeignKey, Integer, DateTime, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.db.db import Base, UUIDPrimaryKeyMixin, TimestampMixin


class Audit(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "audits"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    executive_id: Mapped[uuid.UUID | None] = mapped_column(
    UUID(as_uuid=True),
    ForeignKey("executives.id", ondelete="SET NULL"),
    nullable=True,
    index=True,
    )

    # key columns for quick access without parsing JSON
    score_global: Mapped[int] = mapped_column(Integer, nullable=False)
    score_entreprise: Mapped[int] = mapped_column(Integer, nullable=False)
    score_dirigeant: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dirigeant_present: Mapped[bool] = mapped_column(default=False)

    # full AI output stored as-is
    score_detail: Mapped[dict] = mapped_column(JSONB, nullable=False)
    analyse_ia: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # raw LinkedIn JSON sent to AI — useful for reprocessing later
    linkedin_data: Mapped[dict] = mapped_column(JSONB, nullable=False)

    company: Mapped["Company"] = relationship(back_populates="audits")
    recommendations: Mapped[list["Recommendation"]] = relationship(
        back_populates="audit",
        cascade="all, delete-orphan",
    )