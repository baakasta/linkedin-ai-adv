import uuid
from datetime import datetime, timedelta, UTC
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models.audit import Audit
from backend.models.recommendation import Recommendation
from backend.models.optimization import Optimization
from backend.models.generation import Generation
from backend.models.calendar import Calendar, CalendarSlot


async def build_dashboard(db: AsyncSession, company_id: uuid.UUID) -> dict:
    # --- 1. Audits -----------------------------------------------------------
    audits = (
        await db.execute(
            select(Audit)
            .where(Audit.company_id == company_id)
            .order_by(Audit.created_at)
        )
    ).scalars().all()

    linkedin_score = audits[-1].score_global if audits else None

    score_evolution = [
        {
            "date": a.created_at,
            "score_global": a.score_global,
            "score_entreprise": a.score_entreprise,
            "score_dirigeant": a.score_dirigeant,
        }
        for a in audits
    ]

    # --- 2. Engagement (from latest audit linkedin_data) ---------------------
    pubs = []
    if audits:
        pubs = (
            (audits[-1].linkedin_data or {}).get("entreprise") or {}
        ).get("publications") or []

    total_publications = len(pubs)
    total_reactions = sum(p.get("reactions", 0) for p in pubs)
    total_comments = sum(p.get("commentaires", 0) for p in pubs)
    total_shares = sum(p.get("partages", 0) for p in pubs)
    avg_engagement = (
        round((total_reactions + total_comments + total_shares) / total_publications, 1)
        if total_publications
        else 0.0
    )

    engagement = {
        "total_publications": total_publications,
        "total_reactions": total_reactions,
        "total_comments": total_comments,
        "total_shares": total_shares,
        "avg_engagement": avg_engagement,
    }

    # --- 3. Recommendations priority breakdown -------------------------------
    audit_ids = [a.id for a in audits]
    recs = []
    if audit_ids:
        recs = (
            await db.execute(
                select(Recommendation).where(Recommendation.audit_id.in_(audit_ids))
            )
        ).scalars().all()

    prio = {"CRITIQUE": 0, "IMPORTANTE": 0, "OPTIMISATION": 0}
    for r in recs:
        prio[r.priorite.value] = prio.get(r.priorite.value, 0) + 1

    recommendations_priority = {
        "critique": prio.get("CRITIQUE", 0),
        "importante": prio.get("IMPORTANTE", 0),
        "optimisation": prio.get("OPTIMISATION", 0),
    }

    # --- 4. Optimization progression ----------------------------------------
    rec_ids = [r.id for r in recs]
    opts = []
    if rec_ids:
        opts = (
            await db.execute(
                select(Optimization).where(Optimization.recommendation_id.in_(rec_ids))
            )
        ).scalars().all()

    decision_counts = {"accept": 0, "modify": 0, "reject": 0, "pending": 0}
    for o in opts:
        if o.decision:
            decision_counts[o.decision] = decision_counts.get(o.decision, 0) + 1
        else:
            decision_counts["pending"] += 1

    optimization_progression = {
        "total": len(opts),
        "accepted": decision_counts["accept"],
        "modified": decision_counts["modify"],
        "rejected": decision_counts["reject"],
        "pending": decision_counts["pending"],
    }

    # --- 5. Publication frequency (last 30 days) -----------------------------
    cutoff = datetime.now(UTC) - timedelta(days=30)
    pub_count = 0
    if company_id:
        pub_count = (
            await db.execute(
                select(func.count(Generation.id))
                .where(Generation.company_id == company_id)
                .where(Generation.created_at >= cutoff)
            )
        ).scalar() or 0

    # --- 6. Objectives tracking ---------------------------------------------
    score_improvement = None
    if len(audits) >= 2:
        score_improvement = audits[-1].score_global - audits[0].score_global

    total_recs = len(recs)
    recs_with_opt_decision = len(
        [r for r in recs if any(o.decision for o in opts if o.recommendation_id == r.id)]
    )
    completion_rate = (
        round(recs_with_opt_decision / total_recs * 100, 1) if total_recs else 0.0
    )

    objectives_tracking = {
        "score_improvement": score_improvement,
        "total_recommendations": total_recs,
        "total_optimizations": len(opts),
        "completion_rate": completion_rate,
    }

    return {
        "company_id": company_id,
        "linkedin_score": linkedin_score,
        "score_evolution": score_evolution,
        "engagement": engagement,
        "publication_frequency": pub_count,
        "recommendations_priority": recommendations_priority,
        "optimization_progression": optimization_progression,
        "objectives_tracking": objectives_tracking,
    }
