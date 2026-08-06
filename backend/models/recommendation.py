import uuid
from sqlalchemy import UUID, ForeignKey, String, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum
from backend.db.db import Base, UUIDPrimaryKeyMixin, TimestampMixin


class RecommendationPriority(str, enum.Enum):
    CRITIQUE = "CRITIQUE"
    IMPORTANTE = "IMPORTANTE"
    OPTIMISATION = "OPTIMISATION"


class Recommendation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "recommendations"

    audit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("audits.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # from AI output
    critere_code: Mapped[str] = mapped_column(String(100), nullable=False)
    categorie: Mapped[str] = mapped_column(String(100), nullable=False)
    priorite: Mapped[RecommendationPriority] = mapped_column(
        Enum(RecommendationPriority, name="recommendation_priority"),
        nullable=False,
    )
    action: Mapped[str] = mapped_column(Text, nullable=False)
    raison: Mapped[str] = mapped_column(Text, nullable=False)

    audit: Mapped["Audit"] = relationship(back_populates="recommendations")
    optimizations: Mapped[list["Optimization"]] = relationship(
        back_populates="recommendation",
        cascade="all, delete-orphan",
    )