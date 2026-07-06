from datetime import datetime
import uuid
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import UUID,DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./linkedin_ai_advisor.db"

engine = create_async_engine(SQLALCHEMY_DATABASE_URL)
    
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


class UUIDPrimaryKeyMixin:
    id: Mapped[uuid.UUID] = mapped_column(
    UUID(as_uuid=True),
    primary_key=True,
    default=uuid.uuid4,
    index=True,
)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session