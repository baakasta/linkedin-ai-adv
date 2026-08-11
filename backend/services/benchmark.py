from __future__ import annotations

BENCHMARK_CRITERIA: dict[str, dict] = {
    "frequence_publication": {
        "libelle": "Frequence de publication",
        "criteres": ["frequence_publication"],
    },
    "engagement": {
        "libelle": "Taux d'engagement",
        "criteres": ["engagement"],
    },
    "strategie_editoriale": {
        "libelle": "Strategie editoriale",
        "criteres": ["publications_entreprise"],
    },
    "branding": {
        "libelle": "Branding",
        "criteres": ["logo", "banniere", "slogan"],
    },
    "positionnement": {
        "libelle": "Positionnement",
        "criteres": ["description_entreprise", "services"],
    },
    "mots_cles": {
        "libelle": "Mots-cles",
        "criteres": ["seo_mots_cles"],
    },
}

NOTE_MAX: dict[str, int] = {
    "frequence_publication": 2,
    "engagement": 2,
    "publications_entreprise": 3,
    "logo": 1,
    "banniere": 1,
    "slogan": 2,
    "description_entreprise": 3,
    "services": 2,
    "seo_mots_cles": 2,
}


def evaluations_index(analyse_ia: dict) -> dict[str, dict]:
    index: dict[str, dict] = {}
    for evaluation in analyse_ia.get("evaluations", []):
        code = evaluation.get("critere") or evaluation.get("critere_code")
        if code:
            index[str(code)] = evaluation
    return index


def ratio_for_criterion(evaluations: dict[str, dict], critere_codes: list[str]) -> int | None:
    total = 0
    max_total = 0
    for code in critere_codes:
        note_max = NOTE_MAX.get(code)
        if note_max is None:
            continue
        max_total += note_max
        evaluation = evaluations.get(code)
        if not evaluation:
            continue
        niveau = str(evaluation.get("niveau", "")).strip().lower()
        if niveau == "" or niveau == "non_evaluable":
            continue
        try:
            value = int(niveau)
        except (TypeError, ValueError):
            continue
        total += max(0, min(value, note_max))
    if max_total == 0:
        return None
    return round(total / max_total * 100)


def build_benchmark(target_analyse: dict, competitor_analyses: list[dict]) -> dict:
    target_index = evaluations_index(target_analyse)
    competitor_indexes = [evaluations_index(analyse) for analyse in competitor_analyses]

    scores_par_critere: dict[str, dict] = {}
    points_forts: list[str] = []
    points_faibles: list[str] = []
    recommandations: list[dict] = []

    for code, meta in BENCHMARK_CRITERIA.items():
        target_ratio = ratio_for_criterion(target_index, meta["criteres"])
        competitor_ratios = [
            ratio
            for ratio in (ratio_for_criterion(index, meta["criteres"]) for index in competitor_indexes)
            if ratio is not None
        ]
        if target_ratio is None and not competitor_ratios:
            continue

        moyenne = round(sum(competitor_ratios) / len(competitor_ratios)) if competitor_ratios else None

        scores_par_critere[code] = {
            "libelle": meta["libelle"],
            "entreprise": target_ratio,
            "moyenne_concurrents": moyenne,
        }

        if target_ratio is None or moyenne is None:
            continue

        libelle = meta["libelle"]
        if target_ratio > moyenne:
            points_forts.append(
                f"{libelle} : score de {target_ratio}% (moyenne des concurrents {moyenne}%)"
            )
            continue

        if target_ratio < moyenne:
            points_faibles.append(
                f"{libelle} : score de {target_ratio}% contre {moyenne}% chez les concurrents"
            )
            gap = moyenne - target_ratio
            if gap >= 20:
                priorite = "CRITIQUE"
            elif gap >= 10:
                priorite = "IMPORTANTE"
            else:
                priorite = "OPTIMISATION"
            recommandations.append(
                {
                    "priorite": priorite,
                    "action": f"Ameliorer {libelle.lower()} pour rattraper les concurrents",
                    "raison": (
                        f"Ecart de {gap} points avec la moyenne des concurrents "
                        f"({target_ratio}% contre {moyenne}%)"
                    ),
                }
            )

    target_ratios = [
        score["entreprise"]
        for score in scores_par_critere.values()
        if score["entreprise"] is not None
    ]
    score_benchmark = round(sum(target_ratios) / len(target_ratios)) if target_ratios else None

    recommandations.sort(key=lambda r: {"CRITIQUE": 0, "IMPORTANTE": 1, "OPTIMISATION": 2}[r["priorite"]])

    return {
        "score_benchmark": score_benchmark,
        "scores_par_critere": scores_par_critere,
        "points_forts": points_forts,
        "points_faibles": points_faibles,
        "recommandations": recommandations,
    }
