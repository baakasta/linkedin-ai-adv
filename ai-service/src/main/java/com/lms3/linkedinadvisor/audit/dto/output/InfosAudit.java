package com.lms3.linkedinadvisor.audit.dto.output;

public record InfosAudit(
        String auditId,
        String extractionId,             // relie au JSON d'entrée
        String entrepriseId,
        String dateAudit,
        String versionSchema,
        String versionGrille,
        MoteurIa moteurIa
) {}
