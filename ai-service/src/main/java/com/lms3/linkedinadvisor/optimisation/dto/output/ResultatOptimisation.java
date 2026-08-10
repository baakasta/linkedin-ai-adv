package com.lms3.linkedinadvisor.optimisation.dto.output;

import com.fasterxml.jackson.annotation.JsonAlias;

import java.util.List;

public record ResultatOptimisation(
        String typeElement,
        String contenuOriginal,
        List<String> faiblessesCorrigees,
        List<VarianteOptimisee> variantes,
        @JsonAlias({"marqueurs_acompleter", "marqueursAcompleter","marqueurs"})
        List<String> marqueurs,
        List<String> ameliorationsApportees,
        VarianteRecommandee varianteRecommandee
) {}
