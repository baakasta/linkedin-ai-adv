package com.lms3.linkedinadvisor.audit.dto.output;

import java.util.List;

public record ResultatAudit(
        InfosAudit audit,
        int scoreGlobal,                 // 0..100, calculé par le backend
        int scoreMax,                    // 100
        List<ScoreCategorie> scoresCategories,
        List<String> pointsForts,
        List<String> pointsFaibles,
        List<Recommandation> recommandations,
        String synthese
) {}
