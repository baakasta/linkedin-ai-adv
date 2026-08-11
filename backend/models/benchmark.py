import uuid
from sqlalchemy import UUID, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.db.db import Base, UUIDPrimaryKeyMixin, TimestampMixin


class Benchmark(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "benchmarks"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # competitor audits used for the comparison (target excluded)
    audit_ids: Mapped[list] = mapped_column(JSONB, nullable=False)

    # full computed comparison output
    resultat: Mapped[dict] = mapped_column(JSONB, nullable=False)

    company: Mapped["Company"] = relationship(back_populates="benchmarks")
