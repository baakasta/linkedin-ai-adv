package com.lms3.linkedinadvisor.audit.dto.output;

public record MoteurIa(
        String fournisseur,
        String modele,
        double temperature
) {}
