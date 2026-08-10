package com.lms3.linkedinadvisor.optimisation.dto.output;

public record VarianteOptimisee(
        String angle,                // la strategie (expertise, benefice, differenciation...)
        String contenu,              // le texte reecrit
        String explication           // pourquoi cette version
) {}
