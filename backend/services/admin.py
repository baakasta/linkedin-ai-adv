from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
from backend.models.user import User, Account
from backend.models.company import Company
from backend.models.executive import Executive
from backend.models.audit import Audit
from backend.models.recommendation import Recommendation
from backend.models.optimization import Optimization
from backend.models.generation import Generation
from backend.models.benchmark import Benchmark
from backend.models.watch import Watch
from backend.models.subscription import Subscription, PlanTier, SubscriptionStatus
from backend.schemas.adminschema import AdminStats, AccountUsage


async def get_platform_stats(db: AsyncSession) -> AdminStats:
    total_users = (await db.execute(select(func.count(User.id)))).scalar() or 0
    active_users = (await db.execute(
        select(func.count(User.id)).where(User.is_active == True)
    )).scalar() or 0
    total_accounts = (await db.execute(select(func.count(Account.id)))).scalar() or 0
    total_companies = (await db.execute(select(func.count(Company.id)))).scalar() or 0
    total_executives = (await db.execute(select(func.count(Executive.id)))).scalar() or 0
    total_audits = (await db.execute(select(func.count(Audit.id)))).scalar() or 0
    total_optimizations = (await db.execute(select(func.count(Optimization.id)))).scalar() or 0
    total_generations = (await db.execute(select(func.count(Generation.id)))).scalar() or 0
    total_benchmarks = (await db.execute(select(func.count(Benchmark.id)))).scalar() or 0
    total_watches = (await db.execute(select(func.count(Watch.id)))).scalar() or 0

    tier_rows = (await db.execute(
        select(Subscription.plan_tier, func.count(Subscription.id))
        .group_by(Subscription.plan_tier)
    )).all()
    subscriptions_by_tier = {row[0].value: row[1] for row in tier_rows}

    status_rows = (await db.execute(
        select(Subscription.status, func.count(Subscription.id))
        .group_by(Subscription.status)
    )).all()
    subscriptions_by_status = {row[0].value: row[1] for row in status_rows}

    return AdminStats(
        total_users=total_users,
        active_users=active_users,
        total_accounts=total_accounts,
        total_companies=total_companies,
        total_executives=total_executives,
        total_audits=total_audits,
        total_optimizations=total_optimizations,
        total_generations=total_generations,
        total_benchmarks=total_benchmarks,
        total_watches=total_watches,
        subscriptions_by_tier=subscriptions_by_tier,
        subscriptions_by_status=subscriptions_by_status,
    )


async def get_account_usage(db: AsyncSession) -> list[AccountUsage]:
    accounts = (await db.execute(
        select(Account)
        .options(selectinload(Account.subscription))
    )).scalars().all()

    result = []
    for account in accounts:
        account_company_ids = (await db.execute(
            select(Company.id).where(Company.account_id == account.id)
        )).scalars().all()

        if not account_company_ids:
            result.append(AccountUsage(
                account_id=account.id,
                account_name=account.name,
                plan_tier=account.subscription.plan_tier if account.subscription else PlanTier.DECOUVERTE,
                audit_count=0,
                optimization_count=0,
                generation_count=0,
                benchmark_count=0,
                watch_count=0,
            ))
            continue

        audit_count = (await db.execute(
            select(func.count(Audit.id)).where(Audit.company_id.in_(account_company_ids))
        )).scalar() or 0

        recommendation_ids = (await db.execute(
            select(Recommendation.id).where(Recommendation.audit_id.in_(
                select(Audit.id).where(Audit.company_id.in_(account_company_ids))
            ))
        )).scalars().all()

        optimization_count = 0
        if recommendation_ids:
            optimization_count = (await db.execute(
                select(func.count(Optimization.id)).where(Optimization.recommendation_id.in_(recommendation_ids))
            )).scalar() or 0

        generation_count = (await db.execute(
            select(func.count(Generation.id)).where(Generation.company_id.in_(account_company_ids))
        )).scalar() or 0

        benchmark_count = (await db.execute(
            select(func.count(Benchmark.id)).where(Benchmark.company_id.in_(account_company_ids))
        )).scalar() or 0

        watch_count = (await db.execute(
            select(func.count(Watch.id)).where(Watch.company_id.in_(account_company_ids))
        )).scalar() or 0

        result.append(AccountUsage(
            account_id=account.id,
            account_name=account.name,
            plan_tier=account.subscription.plan_tier if account.subscription else PlanTier.DECOUVERTE,
            audit_count=audit_count,
            optimization_count=optimization_count,
            generation_count=generation_count,
            benchmark_count=benchmark_count,
            watch_count=watch_count,
        ))

    return result
