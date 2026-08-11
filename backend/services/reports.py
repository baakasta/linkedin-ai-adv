from __future__ import annotations

from datetime import datetime
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

BRAND = colors.HexColor("#0B3D91")
LIGHT = colors.HexColor("#F2F5FA")
BORDER = colors.HexColor("#CCCCCC")

_MOIS = [
    "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre",
]


def _safe(text: object) -> str:
    if text is None:
        return ""
    value = str(text)
    try:
        value.encode("cp1252")
        return value
    except UnicodeEncodeError:
        return value.encode("cp1252", errors="replace").decode("cp1252")


def _styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "ReportTitle", parent=base["Title"], fontSize=18, spaceAfter=4,
            textColor=BRAND,
        ),
        "subtitle": ParagraphStyle(
            "ReportSubtitle", parent=base["Normal"], fontSize=10, textColor=colors.HexColor("#555555"),
            spaceAfter=14,
        ),
        "h": ParagraphStyle(
            "ReportH", parent=base["Heading2"], fontSize=13, spaceBefore=14, spaceAfter=6,
            textColor=BRAND,
        ),
        "normal": ParagraphStyle(
            "ReportNormal", parent=base["Normal"], fontSize=9.5, leading=13,
        ),
        "bullet": ParagraphStyle(
            "ReportBullet", parent=base["Normal"], fontSize=9.5, leading=13, leftIndent=10, bulletIndent=2,
        ),
    }


def _table(header: list[str], rows: list[list], col_widths: list[float] | None = None) -> Table:
    s = _styles()
    header_style = ParagraphStyle(
        "ReportCellHeader", parent=s["normal"], fontSize=9, leading=11,
        fontName="Helvetica-Bold", textColor=colors.white,
    )
    cell_style = ParagraphStyle(
        "ReportCell", parent=s["normal"], fontSize=8.5, leading=11,
    )

    def _wrap(value: object, style) -> object:
        if isinstance(value, Paragraph):
            return value
        return Paragraph(_safe(value), style)

    data = (
        [[_wrap(h, header_style) for h in header]]
        + [[_wrap(c, cell_style) for c in row] for row in rows]
    )
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), BRAND),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 1), (-1, -1), 8.5),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
                ("GRID", (0, 0), (-1, -1), 0.4, BORDER),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def _score_cards(items: list[tuple[str, object, object]]) -> Table:
    rows = [[Paragraph(_safe(label), _styles()["normal"]), _safe(value)] for label, value, _ in items]
    table = Table(rows, colWidths=[110, 90])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), LIGHT),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 0.4, BORDER),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def _render(story: list, title: str) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        title=_safe(title),
    )
    doc.build(story)
    return buffer.getvalue()


def audit_report_pdf(
    company_name: str,
    audit,
    recommendations: list,
) -> bytes:
    s = _styles()
    analyse = audit.analyse_ia or {}
    evaluations = analyse.get("evaluations", [])
    score_detail = audit.score_detail or {}

    story = [
        Paragraph(_safe("Rapport d'audit LinkedIn"), s["title"]),
        Paragraph(
            _safe(f"{company_name} — Audit du {audit.created_at:%d/%m/%Y}"),
            s["subtitle"],
        ),
    ]

    story.append(Paragraph("Scores", s["h"]))
    score_items = [
        ("Score global", f"{audit.score_global}/100", score_detail.get("score_global")),
        ("Score entreprise", f"{audit.score_entreprise}/100", score_detail.get("score_entreprise")),
    ]
    if audit.score_dirigeant is not None:
        score_items.append(("Score dirigeant", f"{audit.score_dirigeant}/100", score_detail.get("score_dirigeant")))
    else:
        score_items.append(("Score dirigeant", "Non évalué", None))
    story.append(_score_cards(score_items))
    story.append(Spacer(1, 6))

    story.append(Paragraph("Évaluations par critère", s["h"]))
    if evaluations:
        rows = [
            [
                _safe(e.get("categorie", "")),
                _safe(e.get("critere", "")),
                _safe(e.get("niveau", "")),
                _safe(e.get("justification", "")),
            ]
            for e in evaluations
        ]
        story.append(_table(
            ["Catégorie", "Critère", "Niveau", "Justification"],
            rows,
            col_widths=[55, 60, 25, 110],
        ))
    else:
        story.append(Paragraph("Aucune évaluation disponible.", s["normal"]))

    story.append(Paragraph("Recommandations", s["h"]))
    if recommendations:
        rows = [
            [_safe(r.priorite.value if hasattr(r.priorite, "value") else r.priorite), _safe(r.action), _safe(r.raison)]
            for r in recommendations
        ]
        story.append(_table(["Priorité", "Action", "Raison"], rows, col_widths=[45, 90, 115]))
    else:
        story.append(Paragraph("Aucune recommandation.", s["normal"]))

    return _render(story, f"Audit {company_name}")


def benchmark_report_pdf(company_name: str, benchmark) -> bytes:
    s = _styles()
    resultat = benchmark.resultat or {}

    story = [
        Paragraph("Rapport de benchmark concurrentiel", s["title"]),
        Paragraph(
            _safe(f"{company_name} — Benchmark du {benchmark.created_at:%d/%m/%Y}"),
            s["subtitle"],
        ),
    ]

    score = resultat.get("score_benchmark")
    story.append(Paragraph("Score benchmark", s["h"]))
    story.append(_score_cards([("Score benchmark", f"{score}/100" if score is not None else "Non évalué", score)]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("Comparaison par critère", s["h"]))
    scores = resultat.get("scores_par_critere", {})
    rows = []
    for code, data in scores.items():
        entreprise = data.get("entreprise")
        moyenne = data.get("moyenne_concurrents")
        rows.append([
            _safe(data.get("libelle", code)),
            f"{entreprise}%" if entreprise is not None else "-",
            f"{moyenne}%" if moyenne is not None else "-",
        ])
    story.append(_table(
        ["Critère", "Entreprise", "Moyenne des concurrents"],
        rows,
        col_widths=[130, 60, 60],
    ))

    story.append(Paragraph("Points forts", s["h"]))
    for item in resultat.get("points_forts", []):
        story.append(Paragraph(_safe(f"• {item}"), s["bullet"]))
    if not resultat.get("points_forts"):
        story.append(Paragraph("Aucun.", s["normal"]))

    story.append(Paragraph("Points faibles", s["h"]))
    for item in resultat.get("points_faibles", []):
        story.append(Paragraph(_safe(f"• {item}"), s["bullet"]))
    if not resultat.get("points_faibles"):
        story.append(Paragraph("Aucun.", s["normal"]))

    story.append(Paragraph("Recommandations", s["h"]))
    reco = resultat.get("recommandations", [])
    if reco:
        rows = [
            [_safe(r.get("priorite", "")), _safe(r.get("action", "")), _safe(r.get("raison", ""))]
            for r in reco
        ]
        story.append(_table(["Priorité", "Action", "Raison"], rows, col_widths=[45, 90, 115]))
    else:
        story.append(Paragraph("Aucune recommandation.", s["normal"]))

    return _render(story, f"Benchmark {company_name}")


def monthly_report_pdf(
    company_name: str,
    month: str,
    summary: dict,
    audits: list,
    benchmarks: list,
    generations: list,
    optimizations: list,
) -> bytes:
    s = _styles()
    try:
        year, month_num = month.split("-")
        month_label = f"{_MOIS[int(month_num) - 1]} {year}"
    except (ValueError, IndexError):
        month_label = month

    story = [
        Paragraph("Synthèse mensuelle", s["title"]),
        Paragraph(_safe(f"{company_name} — {month_label}"), s["subtitle"]),
    ]

    story.append(Paragraph("Activité du mois", s["h"]))
    story.append(_table(
        ["Élément", "Nombre"],
        [
            ["Audits réalisés", str(summary.get("audits", 0))],
            ["Optimisations", str(summary.get("optimizations", 0))],
            ["Contenus générés", str(summary.get("generations", 0))],
            ["Benchmarks", str(summary.get("benchmarks", 0))],
        ],
        col_widths=[150, 60],
    ))

    story.append(Paragraph("Historique des audits", s["h"]))
    if audits:
        rows = [
            [
                _safe(f"{a.created_at:%d/%m/%Y}" if a.created_at else ""),
                str(a.score_global),
                str(a.score_entreprise),
                str(a.score_dirigeant) if a.score_dirigeant is not None else "-",
            ]
            for a in audits
        ]
        story.append(_table(
            ["Date", "Score global", "Score entreprise", "Score dirigeant"],
            rows,
            col_widths=[60, 50, 50, 50],
        ))
    else:
        story.append(Paragraph("Aucun audit sur cette période.", s["normal"]))

    story.append(Paragraph("Benchmarks", s["h"]))
    if benchmarks:
        rows = [
            [
                _safe(f"{b.created_at:%d/%m/%Y}" if b.created_at else ""),
                str((b.resultat or {}).get("score_benchmark", "-")),
            ]
            for b in benchmarks
        ]
        story.append(_table(["Date", "Score benchmark"], rows, col_widths=[100, 60]))
    else:
        story.append(Paragraph("Aucun benchmark sur cette période.", s["normal"]))

    if optimizations or generations:
        story.append(PageBreak())
        story.append(Paragraph("Optimisations", s["h"]))
        if optimizations:
            rows = [
                [_safe(f"{o.created_at:%d/%m/%Y}" if o.created_at else ""), _safe(o.type_element)]
                for o in optimizations
            ]
            story.append(_table(["Date", "Élément optimisé"], rows, col_widths=[80, 80]))
        story.append(Paragraph("Contenus générés", s["h"]))
        if generations:
            rows = [
                [_safe(f"{g.created_at:%d/%m/%Y}" if g.created_at else ""), _safe(g.type_contenu)]
                for g in generations
            ]
            story.append(_table(["Date", "Type de contenu"], rows, col_widths=[80, 80]))

    return _render(story, f"Synthèse {company_name} {month_label}")
