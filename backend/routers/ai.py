from typing import Annotated
import uuid
import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.db.db import get_db
from backend.models.user import User
from backend.models.company import Company
from backend.models.audit import Audit
from backend.models.recommendation import Recommendation, RecommendationPriority
from backend.models.optimization import Optimization
from backend.models.generation import Generation
from backend.models.benchmark import Benchmark
from backend.auth import get_current_user
from backend.config import settings
from backend.schemas.auditschema import AuditCreate, AuditResponse, AuditListResponse
from backend.schemas.recommendationschema import RecommendationResponse
from backend.schemas.optimizationschema import (
    OptimizationCreate,
    OptimizationResponse,
    OptimizationDecision,
    OptimizationVerdict,
    OptimizationDecisionRequest,
    OptimizationVerdictResult,
)
from backend.schemas.generationschema import GenerationCreate, GenerationResponse
from backend.schemas.benchmarkschema import BenchmarkCreate, BenchmarkResponse
from backend.services.benchmark import build_benchmark

router = APIRouter()

_PRIORITY_MAP = {
    "CRITIQUE": RecommendationPriority.CRITIQUE,
    "IMPORTANTE": RecommendationPriority.IMPORTANTE,
    "IMPORTANT": RecommendationPriority.IMPORTANTE,
    "OPTIMISATION": RecommendationPriority.OPTIMISATION,
    "OPTIMIZATION": RecommendationPriority.OPTIMISATION,
    "OPTIMISER": RecommendationPriority.OPTIMISATION,
}


def _parse_priority(value: str) -> RecommendationPriority:
    key = str(value or "").strip().upper()
    return _PRIORITY_MAP.get(key, RecommendationPriority.OPTIMISATION)


def _evaluations_by_critere(analyse_ia: dict) -> dict[str, dict]:
    index: dict[str, dict] = {}
    for evaluation in analyse_ia.get("evaluations", []):
        code = evaluation.get("critere") or evaluation.get("critere_code")
        if code:
            index[str(code)] = evaluation
    return index


def _niveau_for_critere(analyse_ia: dict, critere_code: str, default: int = 1) -> int:
    evaluation = _evaluations_by_critere(analyse_ia).get(critere_code)
    if not evaluation:
        return default
    try:
        return int(evaluation.get("niveau", default))
    except (TypeError, ValueError):
        return default


# --- Audit ---

@router.post("/audits", response_model=AuditResponse, status_code=status.HTTP_201_CREATED)
async def create_audit(
    payload: AuditCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # verify company belongs to current user
    company = (await db.execute(
        select(Company).where(Company.id == payload.company_id)
    )).scalars().first()
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    if company.account_id != current_user.account_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your company")

    # call AI module
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{settings.ai_service_url}/api/audits",
                json=payload.linkedin_data,
                timeout=60.0,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"AI service error: {str(exc)}",
            )

    ai_result = response.json()
    score = ai_result["score"]
    analyse = ai_result["analyse_ia"]

    # store audit
    audit = Audit(
        company_id=payload.company_id,
        score_global=score["score_global"],
        score_entreprise=score["score_entreprise"],
        score_dirigeant=score.get("score_dirigeant"),
        dirigeant_present=score.get("dirigeant_present", False),
        score_detail=score,
        analyse_ia=analyse,
        linkedin_data=payload.linkedin_data,
    )
    db.add(audit)
    await db.flush()

    # store recommendations
    eval_index = _evaluations_by_critere(analyse)
    eval_list = analyse.get("evaluations", [])
    reco_list = analyse.get("recommandations", [])

    def match_evaluation(reco: dict, position: int) -> dict | None:
        code = str(reco.get("critere_code") or reco.get("critere") or "").strip()
        categorie = str(reco.get("categorie") or "").strip()
        if code:
            return eval_index.get(code)
        if categorie:
            for evaluation in eval_list:
                if str(evaluation.get("categorie", "")).strip().lower() == categorie.lower():
                    return evaluation
        if len(eval_list) == len(reco_list) and position < len(eval_list):
            # fallback: assume same ordering between evaluations and recommendations
            return eval_list[position]
        return None

    for position, reco in enumerate(reco_list):
        critere_code = str(reco.get("critere_code") or reco.get("critere") or "").strip()
        categorie = str(reco.get("categorie") or "").strip()

        matched_eval = match_evaluation(reco, position)
        if matched_eval:
            critere_code = critere_code or str(
                matched_eval.get("critere_code") or matched_eval.get("critere") or ""
            ).strip()
            categorie = categorie or str(matched_eval.get("categorie", "")).strip()

        recommendation = Recommendation(
            audit_id=audit.id,
            critere_code=critere_code,
            categorie=categorie,
            priorite=_parse_priority(reco.get("priorite")),
            action=str(reco.get("action", "")),
            raison=str(reco.get("raison", "")),
        )
        db.add(recommendation)

    await db.commit()
    await db.refresh(audit)
    return audit


@router.get("/audits/company/{company_id}", response_model=list[AuditListResponse])
async def get_company_audits(
    company_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    company = (await db.execute(
        select(Company).where(Company.id == company_id)
    )).scalars().first()
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    if company.account_id != current_user.account_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your company")

    result = await db.execute(
        select(Audit)
        .where(Audit.company_id == company_id)
        .order_by(Audit.created_at.desc())
    )
    return result.scalars().all()


@router.get("/audits/{audit_id}", response_model=AuditResponse)
async def get_audit(
    audit_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Audit)
        .options(selectinload(Audit.company))
        .where(Audit.id == audit_id)
    )
    audit = result.scalars().first()
    if not audit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit not found")
    if audit.company.account_id != current_user.account_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your audit")
    return audit


@router.get("/audits/{audit_id}/recommendations", response_model=list[RecommendationResponse])
async def get_audit_recommendations(
    audit_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    audit = (await db.execute(
        select(Audit).options(selectinload(Audit.company)).where(Audit.id == audit_id)
    )).scalars().first()
    if not audit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit not found")
    if audit.company.account_id != current_user.account_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your audit")

    result = await db.execute(
        select(Recommendation).where(Recommendation.audit_id == audit_id)
    )
    return result.scalars().all()


# --- Optimization ---

@router.post("/optimizations", response_model=OptimizationResponse, status_code=status.HTTP_201_CREATED)
async def create_optimization(
    payload: OptimizationCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # verify recommendation exists and belongs to user
    recommendation = (await db.execute(
        select(Recommendation)
        .options(selectinload(Recommendation.audit).selectinload(Audit.company))
        .where(Recommendation.id == payload.recommendation_id)
    )).scalars().first()
    if not recommendation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found")
    if recommendation.audit.company.account_id != current_user.account_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your recommendation")

    # build AI request
    niveau = _niveau_for_critere(recommendation.audit.analyse_ia, recommendation.critere_code)
    ai_payload = {
        "type_element": payload.type_element,
        "contenu_actuel": payload.contenu_original or "",
        "resultat_audit": {
            "critere_code": recommendation.critere_code,
            "niveau": niveau,
            "justification_audit": recommendation.raison,
            "recommandation_id": str(recommendation.id),
        },
        "contexte_entreprise": payload.contexte_entreprise,
    }

    # call AI module
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{settings.ai_service_url}/api/optimisations",
                json=ai_payload,
                timeout=60.0,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"AI service error: {str(exc)}",
            )

    ai_result = response.json()

    optimization = Optimization(
        recommendation_id=payload.recommendation_id,
        type_element=payload.type_element,
        contenu_original=payload.contenu_original,
        contexte_entreprise=payload.contexte_entreprise,
        variantes={"variantes": ai_result.get("variantes", [])},
        variante_recommandee=ai_result.get("variante_recommandee", {}),
        marqueurs=ai_result.get("marqueurs", []),
        faiblesses_corrigees=ai_result.get("faiblesses_corrigees", []),
        ameliorations_apportees=ai_result.get("ameliorations_apportees", []),
    )
    db.add(optimization)
    await db.commit()
    await db.refresh(optimization)
    return optimization


@router.get("/optimizations/{optimization_id}", response_model=OptimizationResponse)
async def get_optimization(
    optimization_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    optimization = (await db.execute(
        select(Optimization)
        .options(
            selectinload(Optimization.recommendation)
            .selectinload(Recommendation.audit)
            .selectinload(Audit.company)
        )
        .where(Optimization.id == optimization_id)
    )).scalars().first()
    if not optimization:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Optimization not found")
    if optimization.recommendation.audit.company.account_id != current_user.account_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your optimization")
    return optimization


def _recommended_content(optimization: Optimization) -> str:
    """Contenu de la variante recommandee (fallback: premiere variante)."""
    recommended = optimization.variante_recommandee or {}
    angle = recommended.get("angle")
    for v in (optimization.variantes or {}).get("variantes", []):
        if v.get("angle") == angle and v.get("contenu"):
            return v["contenu"]
    variants = (optimization.variantes or {}).get("variantes", [])
    if variants and variants[0].get("contenu"):
        return variants[0]["contenu"]
    return optimization.contenu_original or ""


def _final_content_from_result(ai_result: dict) -> str:
    recommended = ai_result.get("variante_recommandee") or {}
    angle = recommended.get("angle")
    for v in ai_result.get("variantes", []):
        if v.get("angle") == angle and v.get("contenu"):
            return v["contenu"]
    variants = ai_result.get("variantes", [])
    if variants and variants[0].get("contenu"):
        return variants[0]["contenu"]
    return ""


async def _call_ai_optimisation(ai_payload: dict) -> dict:
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{settings.ai_service_url}/api/optimisations",
                json=ai_payload,
                timeout=60.0,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"AI service error: {str(exc)}",
            )
    return response.json()


@router.patch("/optimizations/decisions", response_model=list[OptimizationVerdictResult])
async def decide_optimizations(
    payload: OptimizationDecisionRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Traite en lot les decisions de l'utilisateur sur ses optimisations:
    accept -> finalise la variante recommandee via le module IA,
    modify -> l'IA interprete la consigne fournie par l'utilisateur,
    reject -> marque simplement la recommandation comme rejetee."""
    results: list[OptimizationVerdictResult] = []

    for verdict in payload.verdicts:
        if verdict.decision == OptimizationDecision.MODIFY and not (verdict.prompt or "").strip():
            results.append(OptimizationVerdictResult(
                optimization_id=verdict.optimization_id,
                decision=verdict.decision,
                status="error",
                message="Le champ prompt est requis pour la decision modify",
            ))
            continue

        optimization = (await db.execute(
            select(Optimization)
            .options(
                selectinload(Optimization.recommendation)
                .selectinload(Recommendation.audit)
                .selectinload(Audit.company)
            )
            .where(Optimization.id == verdict.optimization_id)
        )).scalars().first()
        if not optimization or (
            optimization.recommendation.audit.company.account_id != current_user.account_id
        ):
            results.append(OptimizationVerdictResult(
                optimization_id=verdict.optimization_id,
                decision=verdict.decision,
                status="error",
                message="Optimization not found or not yours",
            ))
            continue

        if verdict.decision == OptimizationDecision.REJECT:
            optimization.decision = OptimizationDecision.REJECT.value
            optimization.contenu_final = None
            results.append(OptimizationVerdictResult(
                optimization_id=verdict.optimization_id,
                decision=verdict.decision,
                status="success",
                message=f"Recommandation {optimization.id} rejetee",
            ))
            continue

        rec = optimization.recommendation
        base_content = _recommended_content(optimization)
        niveau = _niveau_for_critere(rec.audit.analyse_ia, rec.critere_code)

        if verdict.decision == OptimizationDecision.ACCEPT:
            consigne = (
                "L'utilisateur a accepte la variante recommandee fournie dans "
                "contenu_actuel. Finalise-la : corrige les eventuelles fautes "
                "et ameliore la fluidite sans changer le sens ni le fond."
            )
        else:
            consigne = verdict.prompt

        ai_payload = {
            "type_element": optimization.type_element,
            "contenu_actuel": base_content,
            "resultat_audit": {
                "critere_code": rec.critere_code,
                "niveau": niveau,
                "justification_audit": rec.raison,
                "recommandation_id": str(rec.id),
            },
            "contexte_entreprise": optimization.contexte_entreprise or {},
            "consigne_utilisateur": consigne,
        }

        try:
            ai_result = await _call_ai_optimisation(ai_payload)
        except HTTPException as exc:
            results.append(OptimizationVerdictResult(
                optimization_id=verdict.optimization_id,
                decision=verdict.decision,
                status="error",
                message=exc.detail,
            ))
            continue

        contenu_final = _final_content_from_result(ai_result)
        optimization.decision = verdict.decision.value
        optimization.contenu_final = contenu_final or None
        optimization.variantes = {"variantes": ai_result.get("variantes", [])}
        optimization.variante_recommandee = ai_result.get("variante_recommandee", {})
        optimization.marqueurs = ai_result.get("marqueurs", [])
        optimization.faiblesses_corrigees = ai_result.get("faiblesses_corrigees", [])
        optimization.ameliorations_apportees = ai_result.get("ameliorations_apportees", [])

        message = (
            f"Recommandation {optimization.id} finalisee"
            if verdict.decision == OptimizationDecision.ACCEPT
            else f"Recommandation {optimization.id} modifiee selon votre consigne"
        )
        results.append(OptimizationVerdictResult(
            optimization_id=verdict.optimization_id,
            decision=verdict.decision,
            status="success",
            message=message,
            result=ai_result,
        ))

    await db.commit()
    return results


# --- Generation ---

@router.post("/generations", response_model=GenerationResponse, status_code=status.HTTP_201_CREATED)
async def create_generation(
    payload: GenerationCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    company = (await db.execute(
        select(Company).where(Company.id == payload.company_id)
    )).scalars().first()
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    if company.account_id != current_user.account_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your company")

    # build AI request
    ai_payload = {
        "type_contenu": payload.type_contenu,
        "brief": payload.brief,
        "contexte_entreprise": payload.contexte_entreprise,
    }

    # call AI module
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{settings.ai_service_url}/api/generations",
                json=ai_payload,
                timeout=60.0,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"AI service error: {str(exc)}",
            )

    ai_result = response.json()

    generation = Generation(
        company_id=payload.company_id,
        type_contenu=payload.type_contenu,
        brief=payload.brief,
        titre_interne=ai_result.get("titre_interne"),
        variantes={"variantes": ai_result.get("variantes", [])},
        marqueurs_a_completer=ai_result.get(
            "marqueurs_a_completer",
            ai_result.get("marqueurs_acompleter", []),
        ),
    )
    db.add(generation)
    await db.commit()
    await db.refresh(generation)
    return generation


@router.get("/generations/{generation_id}", response_model=GenerationResponse)
async def get_generation(
    generation_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    generation = (await db.execute(
        select(Generation)
        .options(selectinload(Generation.company))
        .where(Generation.id == generation_id)
    )).scalars().first()
    if not generation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Generation not found")
    if generation.company.account_id != current_user.account_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your generation")
    return generation


@router.get("/generations/company/{company_id}", response_model=list[GenerationResponse])
async def get_company_generations(
    company_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    company = (await db.execute(
        select(Company).where(Company.id == company_id)
    )).scalars().first()
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    if company.account_id != current_user.account_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your company")

    result = await db.execute(
        select(Generation)
        .where(Generation.company_id == company_id)
        .order_by(Generation.created_at.desc())
    )
    return result.scalars().all()


# --- Benchmark ---

@router.post("/benchmarks", response_model=BenchmarkResponse, status_code=status.HTTP_201_CREATED)
async def create_benchmark(
    payload: BenchmarkCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    company = (await db.execute(
        select(Company).where(Company.id == payload.company_id)
    )).scalars().first()
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    if company.account_id != current_user.account_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your company")

    target_audit = (await db.execute(
        select(Audit)
        .where(Audit.company_id == payload.company_id)
        .order_by(Audit.created_at.desc())
    )).scalars().first()
    if not target_audit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Company has no audit yet — run an audit first",
        )

    competitor_analyses: list[dict] = []
    competitor_ids: list[str] = []
    seen: set[str] = set()
    for audit_id in payload.audit_ids:
        audit_key = str(audit_id)
        if audit_key in seen:
            continue
        seen.add(audit_key)
        audit = (await db.execute(
            select(Audit)
            .options(selectinload(Audit.company))
            .where(Audit.id == audit_id)
        )).scalars().first()
        if not audit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Audit {audit_id} not found",
            )
        if audit.company.account_id != current_user.account_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not your audit",
            )
        if audit.company_id == payload.company_id:
            continue
        competitor_analyses.append(audit.analyse_ia)
        competitor_ids.append(audit_key)

    if not competitor_analyses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide at least one competitor audit from a different company",
        )

    resultat = build_benchmark(target_audit.analyse_ia, competitor_analyses)

    benchmark = Benchmark(
        company_id=payload.company_id,
        audit_ids=[str(audit_id) for audit_id in payload.audit_ids],
        resultat=resultat,
    )
    db.add(benchmark)
    await db.commit()
    await db.refresh(benchmark)
    return benchmark


@router.get("/benchmarks/{benchmark_id}", response_model=BenchmarkResponse)
async def get_benchmark(
    benchmark_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    benchmark = (await db.execute(
        select(Benchmark)
        .options(selectinload(Benchmark.company))
        .where(Benchmark.id == benchmark_id)
    )).scalars().first()
    if not benchmark:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Benchmark not found")
    if benchmark.company.account_id != current_user.account_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your benchmark")
    return benchmark


@router.get("/benchmarks/company/{company_id}", response_model=list[BenchmarkResponse])
async def get_company_benchmarks(
    company_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    company = (await db.execute(
        select(Company).where(Company.id == company_id)
    )).scalars().first()
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    if company.account_id != current_user.account_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your company")

    result = await db.execute(
        select(Benchmark)
        .where(Benchmark.company_id == company_id)
        .order_by(Benchmark.created_at.desc())
    )
    return result.scalars().all()