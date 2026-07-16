import enum
from sqlalchemy import Enum, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import uuid
from sqlalchemy import UUID
from backend.db.db import Base, UUIDPrimaryKeyMixin, TimestampMixin



class PlanTier(str, enum.Enum):
    DECOUVERTE = "decouverte"
    PRO = "pro"
    BUSINESS = "business"


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"


class Subscription(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "subscriptions"

    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        unique=True,   
        nullable=False,
        index=True,
    )
    plan_tier: Mapped[PlanTier] = mapped_column(
        Enum(PlanTier, name="plan_tier"),
        default=PlanTier.DECOUVERTE,
    )
    status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(SubscriptionStatus, name="subscription_status"),
        default=SubscriptionStatus.ACTIVE,
    )
    current_period_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    account: Mapped["Account"] = relationship(back_populates="subscription")
    # Stripe fields — empty for now, filled when billing is built
    #stripe_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    #stripe_subscription_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

  
