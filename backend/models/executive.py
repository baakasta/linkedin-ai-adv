import uuid
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import UUID
from backend.db.db import Base, UUIDPrimaryKeyMixin, TimestampMixin


class Executive(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "executives"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    full_name: Mapped[str] = mapped_column(String(255))
    job_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    company: Mapped["Company"] = relationship(back_populates="executives")