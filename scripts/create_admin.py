import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from backend.models.user import User, Account, UserRole
from backend.models.subscription import Subscription, PlanTier, SubscriptionStatus
from backend.models.company import Company  
from backend.models.executive import Executive  
from backend.models.audit import Audit
from backend.models.recommendation import Recommendation
from backend.models.optimization import Optimization
from backend.models.generation import Generation
from backend.auth import hash_password
from backend.config import settings

engine = create_async_engine(settings.database_url)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def create_admin(
    full_name: str,
    email: str,
    password: str,
    account_name: str,
):
    async with AsyncSessionLocal() as db:
        # check if admin already exists
        existing = (await db.execute(select(User).where(User.email == email))).scalars().first()
        if existing:
            print(f"User {email} already exists")
            return

        account = Account(name=account_name)
        db.add(account)
        await db.flush()

        subscription = Subscription(
            account_id=account.id,
            plan_tier=PlanTier.BUSINESS,
            status=SubscriptionStatus.ACTIVE,
        )
        db.add(subscription)

        admin = User(
            account_id=account.id,
            full_name=full_name,
            email=email.lower(),
            password_hash=hash_password(password),
            role=UserRole.ADMIN,
        )
        db.add(admin)
        await db.commit()
        print(f"Admin created: {email}")

asyncio.run(create_admin(
    full_name="Admin",
    email="admin@admin.com",
    password="admin",
    account_name="Admin Account",
))