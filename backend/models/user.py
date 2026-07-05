import enum
import uuid
from sqlalchemy import UUID
from sqlalchemy import Boolean, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

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

class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    #hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="user_role"), default=UserRole.OWNER)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    account: Mapped["Account"] = relationship(back_populates="users")
   

