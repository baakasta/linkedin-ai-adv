package com.lms3.linkedinadvisor.audit.dto.output;

public record Recommandation(
        String id,
        String priorite,                 // CRITIQUE | IMPORTANTE | OPTIMISATION
        String categorie,
        String critereCode,
        String titre,
        String detail,
        String statut                    // EN_ATTENTE | ACCEPTEE | REJETEE | APPLIQUEE
) {}
