package com.lms3.linkedinadvisor.audit.service;

import com.lms3.linkedinadvisor.config.GrilleScoringConfig;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Set;

@Service
public class ScoreAggregator {
    private static final double POIDS_ENTREPRISE = 0.70;
    private static final double POIDS_DIRIGEANT = 0.30;

    private static final Set<String> CATEGORIES_DIRIGEANT =
            Set.of("dirigeant", "coherence");

    private final GrilleScoringConfig grille;

    public ScoreAggregator(GrilleScoringConfig grille) {
        this.grille = grille;
    }

    public ResultatScore calculer(Map<String, Integer> notesObtenues,
                                  boolean dirigeantPresent) {

        List<SousScoreCategorie> sousScoresCategories = new ArrayList<>();

        // Accumulateurs par bloc
        int obtenuEntreprise = 0, maxEntreprise = 0;
        int obtenuDirigeant = 0, maxDirigeant = 0;

        for (GrilleScoringConfig.Categorie categorie : grille.getCategories()) {

            boolean estBlocDirigeant = CATEGORIES_DIRIGEANT.contains(categorie.getCode());

            // Si dirigeant absent, on ignore entierement les categories dirigeant.
            if (estBlocDirigeant && !dirigeantPresent) {
                sousScoresCategories.add(new SousScoreCategorie(
                        categorie.getCode(), categorie.getLibelle(),
                        0, 0, null, false));
                continue;
            }

            int obtenuCat = 0, maxCat = 0, nbEvaluables = 0;

            for (GrilleScoringConfig.Critere critere : categorie.getCriteres()) {
                Integer note = notesObtenues.get(critere.getCode());
                if (note == null) {
                    continue; // non_evaluable -> exclu
                }
                int noteBornee = Math.max(0, Math.min(note, critere.getNoteMax()));
                obtenuCat += noteBornee;
                maxCat += critere.getNoteMax();
                nbEvaluables++;
            }

            Integer pourcentageCat = (maxCat > 0)
                    ? Math.round((float) obtenuCat / maxCat * 100)
                    : null;

            sousScoresCategories.add(new SousScoreCategorie(
                    categorie.getCode(), categorie.getLibelle(),
                    obtenuCat, maxCat, pourcentageCat, nbEvaluables > 0));

            // Accumulation dans le bon bloc
            if (estBlocDirigeant) {
                obtenuDirigeant += obtenuCat;
                maxDirigeant += maxCat;
            } else {
                obtenuEntreprise += obtenuCat;
                maxEntreprise += maxCat;
            }
        }

        //Sous - score de chaque bloc(0. .100)
        int scoreEntreprise = (maxEntreprise > 0)
                ? Math.round((float) obtenuEntreprise / maxEntreprise * 100)
                : 0;

        Integer scoreDirigeant = (dirigeantPresent && maxDirigeant > 0)
                ? Math.round((float) obtenuDirigeant / maxDirigeant * 100)
                : null;

        // Score global selon la presence du dirigeant
        int scoreGlobal;
        if (dirigeantPresent && scoreDirigeant != null) {
            scoreGlobal = (int) Math.round(
                    scoreEntreprise * POIDS_ENTREPRISE
                            + scoreDirigeant * POIDS_DIRIGEANT);
        } else {
            scoreGlobal = scoreEntreprise; // 100 % entreprise
        }

        return new ResultatScore(
                scoreGlobal,
                scoreEntreprise,
                scoreDirigeant,
                dirigeantPresent,
                sousScoresCategories
        );
    }

    // ============================================================
    // Objets de resultat (records)
    // ============================================================

    public record ResultatScore(
            int scoreGlobal,            // 0..100
            int scoreEntreprise,        // sous-score bloc entreprise (0..100)
            Integer scoreDirigeant,     // sous-score bloc dirigeant, null si absent
            boolean dirigeantPresent,
            List<SousScoreCategorie> sousScoresCategories
    ) {}

    public record SousScoreCategorie(
            String code,
            String libelle,
            int obtenu,
            int max,
            Integer pourcentage,        // null si categorie non evaluee
            boolean evaluee
    ) {}
}
