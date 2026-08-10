package com.lms3.linkedinadvisor.optimisation.dto.input;

public record ResultatAuditInput(
        String critereCode,
        Integer niveau,              // le niveau obtenu a l'audit
        String justificationAudit,   // le defaut identifie par l'audit
        String recommandationId      // pour mettre a jour le statut ensuite
) {}
