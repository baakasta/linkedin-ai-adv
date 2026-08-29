import uuid
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import UUID
from backend.db.db import Base, UUIDPrimaryKeyMixin, TimestampMixin
from backend.models.generation import Generation
from backend.models.audit import Audit
from backend.models.benchmark import Benchmark
from backend.models.calendar import Calendar
from backend.models.watch import Watch
from backend.models.strategy import Strategy


class Company(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "companies"

    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255))
    linkedin_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    account: Mapped["Account"] = relationship(back_populates="companies")
    executives: Mapped[list["Executive"]] = relationship(back_populates="company", cascade="all, delete-orphan")

    audits: Mapped[list["Audit"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    generations: Mapped[list["Generation"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    benchmarks: Mapped[list["Benchmark"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    calendar: Mapped["Calendar | None"] = relationship(back_populates="company", cascade="all, delete-orphan")
    watches: Mapped[list["Watch"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    strategies: Mapped[list["Strategy"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    conversations: Mapped[list["Conversation"]] = relationship(back_populates="company", cascade="all, delete-orphan")