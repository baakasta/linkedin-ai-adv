from __future__ import annotations
import enum

import uuid
from sqlalchemy import UUID,DateTime, func
from sqlalchemy import Boolean, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime,UTC
from backend.db.db import Base, TimestampMixin, UUIDPrimaryKeyMixin




class UserRole(str, enum.Enum):
    OWNER = "owner"  
    ADMIN = "admin"  
    MEMBER = "member" 


class Account(UUIDPrimaryKeyMixin, TimestampMixin, Base):

    __tablename__ = "accounts"

    name: Mapped[str] = mapped_column(String(255))

    users: Mapped[list["User"]] = relationship(back_populates="account", cascade="all, delete-orphan")
    companies: Mapped[list["Company"]] = relationship(back_populates="account", cascade="all, delete-orphan")  
    subscription: Mapped["Subscription"] = relationship(back_populates="account", uselist=False, cascade="all, delete-orphan")  

class PasswordResetToken(Base,UUIDPrimaryKeyMixin):
    __tablename__ = "password_reset_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )

    user: Mapped[User] = relationship(back_populates="reset_tokens")

class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(200), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="user_role"), default=UserRole.OWNER)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    account: Mapped["Account"] = relationship(back_populates="users")
    reset_tokens: Mapped[list[PasswordResetToken]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


   

