from __future__ import annotations


def _score_label(score_global: int | None) -> str:
    if score_global is None:
        return "non évalué"
    if score_global >= 85:
        return "Excellente"
    if score_global >= 70:
        return "Bonne"
    if score_global >= 50:
        return "Correcte"
    if score_global >= 30:
        return "Faible"
    return "Critique"


def build_strategy_placeholder(company_name: str, score_global: int | None = None) -> dict:
    """Deterministic strategy generation used when the Java AI service is unavailable."""
    niveau = _score_label(score_global)

    axes = [
        {
            "axe": "Positionnement",
            "objectif": f"Affirmer le positionnement B2B de {company_name} sur LinkedIn.",
            "actions": [
                "Optimiser la description de l'entreprise avec des mots-clés métier.",
                "Mettre en avant les services et réalisations clés.",
                "Clarifier la valeur ajoutée face à la concurrence.",
            ],
        },
        {
            "axe": "Autorité",
            "objectif": "Installer une autorité thématique auprès de la cible.",
            "actions": [
                "Publier régulièrement des contenus experts.",
                "Impliquer les dirigeants dans la prise de parole.",
                "Partager des études de cas et des données.",
            ],
        },
        {
            "axe": "Engagement",
            "objectif": "Stimuler l'engagement de la communauté.",
            "actions": [
                "Poser des questions et inciter aux commentaires.",
                "Répondre rapidement aux échanges.",
                "Relayer et commenter les contenus de la cible.",
            ],
        },
        {
            "axe": "Conversion",
            "objectif": "Transformer l'audience en opportunités.",
            "actions": [
                "Créer des appel-à-l'action clairs.",
                "Diriger vers les pages de conversion.",
                "Mesurer les retombées sur les leads.",
            ],
        },
    ]

    planning = {
        "frequence": "3 à 4 publications par semaine",
        "repartition": [
            {"type": "Publication experte", "proportion": "40%"},
            {"type": "Actualité / opinion", "proportion": "20%"},
            {"type": "Preuve sociale", "proportion": "20%"},
            {"type": "Engagement / questions", "proportion": "20%"},
        ],
        "horaires": ["mardi - jeudi, 9h-11h ou 17h-18h"],
    }

    cibles = [
        {
            "segments": ["Directeurs décisionnaires", "Responsables achats", "Influenceurs du secteur"],
            "besoins": ["Enjeux B2B", "Contenus différenciants", "Preuves concrètes"],
        }
    ]

    return {
        "note_globale": score_global,
        "niveau_maturite": niveau,
        "objets": axes,
        "planning": planning,
        "cibles": cibles,
        "sources_placeholders": True,
        "message": (
            "Stratégie générée localement en mode placeholder (service IA Java indisponible). "
            "Elle sera affinée par l'assistant IA une fois intégré."
        ),
    }
