package com.lms3.linkedinadvisor.audit.dto.output;

import java.util.List;

public record ScoreCategorie(
        String code,                     // ex. "completude_page"
        String libelle,
        int poids,                       // ex. 25
        double noteMoyenne,              // 0..10
        double pointsObtenus,            // noteMoyenne/10 * poids
        List<CritereEvalue> criteres
) {}
