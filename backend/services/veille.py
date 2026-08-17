import uuid
from datetime import date, datetime, UTC
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import httpx

from backend.models.watch import Watch
from backend.models.watch_snapshot import WatchSnapshot
from backend.models.watch_alert import WatchAlert
from backend.models.audit import Audit
from backend.models.company import Company
from backend.config import settings


def _extract_metrics(audit: Audit) -> dict:
    """Extract monitoring metrics from an audit's linkedin_data."""
    ent = (audit.linkedin_data or {}).get("entreprise") or {}
    pubs = ent.get("publications") or []

    total_reactions = sum(p.get("reactions", 0) for p in pubs)
    total_comments = sum(p.get("commentaires", 0) for p in pubs)
    total_shares = sum(p.get("partages", 0) for p in pubs)
    pub_count = len(pubs)

    return {
        "score_global": audit.score_global,
        "score_entreprise": audit.score_entreprise,
        "score_dirigeant": audit.score_dirigeant,
        "publications_count": pub_count,
        "total_reactions": total_reactions,
        "total_comments": total_comments,
        "total_shares": total_shares,
        "engagement_rate": round(
            (total_reactions + total_comments + total_shares) / pub_count, 2
        ) if pub_count else 0.0,
    }


def _compare_metrics(prev: dict, curr: dict) -> list[dict]:
    """Compare two snapshots and return alert dicts."""
    alerts = []

    # score changes
    prev_score = prev.get("score_global", 0)
    curr_score = curr.get("score_global", 0)
    delta = curr_score - prev_score

    if delta <= -5:
        alerts.append({
            "alert_type": "score_drop",
            "title": f"Score LinkedIn en baisse de {abs(delta)} points",
            "detail": f"Score passe de {prev_score} a {curr_score}",
            "severity": "warning" if delta > -15 else "critical",
        })
    elif delta >= 5:
        alerts.append({
            "alert_type": "score_improve",
            "title": f"Score LinkedIn en hausse de {delta} points",
            "detail": f"Score passe de {prev_score} a {curr_score}",
            "severity": "info",
        })

    # engagement changes
    prev_eng = prev.get("engagement_rate", 0)
    curr_eng = curr.get("engagement_rate", 0)
    if prev_eng > 0:
        eng_change = (curr_eng - prev_eng) / prev_eng
        if eng_change <= -0.3:
            alerts.append({
                "alert_type": "engagement_drop",
                "title": "Engagement en baisse significative",
                "detail": f"Taux d'engagement: {prev_eng} -> {curr_eng} ({eng_change:.0%})",
                "severity": "warning",
            })
        elif eng_change >= 0.5:
            alerts.append({
                "alert_type": "engagement_spike",
                "title": "Forte hausse de l'engagement",
                "detail": f"Taux d'engagement: {prev_eng} -> {curr_eng} ({eng_change:.0%})",
                "severity": "info",
            })

    return alerts


async def _run_ai_veille_analysis(
    company_name: str,
    company_metrics: dict,
    competitor_data: list[dict],
    snapshots: list[dict],
) -> str | None:
    """Call Mistral to produce a trend/opportunity analysis."""
    prompt = (
        f"Tu es un expert en veille LinkedIn B2B.\n\n"
        f"ENTREPRISE: {company_name}\n"
        f"METRIQUES ACTUELLES: {company_metrics}\n\n"
    )
    if competitor_data:
        prompt += "CONCURRENTS:\n"
        for c in competitor_data:
            prompt += f"- {c['name']}: {c['metrics']}\n"
        prompt += "\n"
    if len(snapshots) >= 2:
        prompt += "HISTORIQUE (plus ancien -> plus recent):\n"
        for s in snapshots:
            prompt += f"- {s['period']}: score={s['metrics'].get('score_global')}, engagement={s['metrics'].get('engagement_rate')}\n"
        prompt += "\n"

    prompt += (
        "Fournis une analyse concise en francais avec:\n"
        "1. Tendances observes (score, engagement, activite)\n"
        "2. Comparaison avec les concurrents\n"
        "3. Opportunites de communication\n"
        "4. Recommandations prioritaires\n"
        "Reponse en texte brut, 200 mots max."
    )

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{settings.ai_service_url}/api/optimisations",
                json={
                    "type_element": "publication",
                    "contenu_actuel": "",
                    "resultat_audit": {"critere_code": "", "niveau": 1, "justification_audit": prompt, "recommandation_id": ""},
                    "contexte_entreprise": {},
                    "consigne_utilisateur": prompt,
                },
                timeout=60.0,
            )
            resp.raise_for_status()
            result = resp.json()
            # extract from first variant
            variantes = result.get("variantes", [])
            if variantes:
                return variantes[0].get("contenu", "")
    except Exception:
        pass
    return None


async def create_snapshot_from_audit(
    db: AsyncSession,
    watch_id: uuid.UUID,
    audit: Audit,
) -> WatchSnapshot:
    """Create a WatchSnapshot from an audit and generate alerts if needed."""
    metrics = _extract_metrics(audit)

    snapshot = WatchSnapshot(
        watch_id=watch_id,
        audit_id=audit.id,
        period=date.today(),
        metrics=metrics,
    )
    db.add(snapshot)
    await db.flush()

    # compare with previous snapshot
    previous = (
        await db.execute(
            select(WatchSnapshot)
            .where(WatchSnapshot.watch_id == watch_id)
            .where(WatchSnapshot.id != snapshot.id)
            .order_by(desc(WatchSnapshot.created_at))
            .limit(1)
        )
    ).scalars().first()

    if previous:
        alerts_data = _compare_metrics(previous.metrics, metrics)
        for a in alerts_data:
            alert = WatchAlert(watch_id=watch_id, **a)
            db.add(alert)

    await db.flush()
    return snapshot


async def build_veille_overview(
    db: AsyncSession,
    watch_id: uuid.UUID,
) -> dict:
    """Build the full veille overview with competitor data and AI analysis."""
    watch = (
        await db.execute(
            select(Watch)
            .options(
                selectinload(Watch.snapshots),
                selectinload(Watch.alerts),
            )
            .where(Watch.id == watch_id)
        )
    ).scalars().first()

    # latest snapshot
    sorted_snapshots = sorted(watch.snapshots, key=lambda s: s.created_at, reverse=True)
    latest_snapshot = sorted_snapshots[0] if sorted_snapshots else None

    # competitor snapshots from their latest audits
    competitor_data = []
    comp_ids = watch.competitor_ids or []
    if comp_ids:
        comp_ids_uuid = [uuid.UUID(cid) if isinstance(cid, str) else cid for cid in comp_ids]
        comp_audits = (
            await db.execute(
                select(Audit)
                .options(selectinload(Audit.company))
                .where(Audit.company_id.in_(comp_ids_uuid))
                .order_by(desc(Audit.created_at))
            )
        ).scalars().all()

        seen = set()
        for a in comp_audits:
            if a.company_id in seen:
                continue
            seen.add(a.company_id)
            competitor_data.append({
                "name": a.company.name,
                "metrics": _extract_metrics(a),
            })

    # recent alerts (last 20)
    recent_alerts = sorted(watch.alerts, key=lambda al: al.created_at, reverse=True)[:20]

    # AI analysis
    company = watch.company
    snapshots_for_ai = [
        {"period": str(s.period), "metrics": s.metrics}
        for s in sorted_snapshots[:5]
    ]
    ai_analysis = await _run_ai_veille_analysis(
        company_name=company.name,
        company_metrics=latest_snapshot.metrics if latest_snapshot else {},
        competitor_data=competitor_data,
        snapshots=snapshots_for_ai,
    )

    return {
        "watch_id": watch.id,
        "company_id": watch.company_id,
        "latest_snapshot": latest_snapshot,
        "competitor_snapshots": competitor_data,
        "recent_alerts": recent_alerts,
        "ai_analysis": ai_analysis,
    }
