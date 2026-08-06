import uuid
from sqlalchemy import UUID, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from backend.db.db import Base, UUIDPrimaryKeyMixin, TimestampMixin


class Optimization(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "optimizations"

    recommendation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("recommendations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    type_element: Mapped[str] = mapped_column(String(100), nullable=False)
    contenu_original: Mapped[str | None] = mapped_column(Text, nullable=True)

    # full AI output — 3 variants + recommended
    variantes: Mapped[dict] = mapped_column(JSONB, nullable=False)
    variante_recommandee: Mapped[dict] = mapped_column(JSONB, nullable=False)
    marqueurs: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    recommendation: Mapped["Recommendation"] = relationship(back_populates="optimizations")
    faiblesses_corrigees: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    ameliorations_apportees: Mapped[list | None] = mapped_column(JSONB, nullable=True)