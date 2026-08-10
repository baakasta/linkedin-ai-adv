package com.lms3.linkedinadvisor.audit.dto.ia;

public record RecommandationIA(
        String priorite,      // "CRITIQUE" | "IMPORTANTE" | "OPTIMISATION"
        String action,
        String raison
) {}
