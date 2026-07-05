import uuid
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import UUID
from backend.db.db import Base, UUIDPrimaryKeyMixin, TimestampMixin


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