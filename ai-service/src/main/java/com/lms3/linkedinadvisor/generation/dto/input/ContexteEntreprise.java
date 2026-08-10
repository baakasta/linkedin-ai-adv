package com.lms3.linkedinadvisor.generation.dto.input;

import java.util.List;

public record ContexteEntreprise(
        String nom,
        String secteur,
        String cibleClient,
        List<String> services,
        String positionnement,
        String tonSouhaite
) {}
