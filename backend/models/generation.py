import uuid
from sqlalchemy import UUID, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from backend.db.db import Base, UUIDPrimaryKeyMixin, TimestampMixin


class Generation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "generations"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    type_contenu: Mapped[str] = mapped_column(String(100), nullable=False)

    # brief sent to AI
    brief: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # full AI output
    variantes: Mapped[dict] = mapped_column(JSONB, nullable=False)
    marqueurs_a_completer: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    company: Mapped["Company"] = relationship(back_populates="generations")
    titre_interne: Mapped[str | None] = mapped_column(String(500), nullable=True)