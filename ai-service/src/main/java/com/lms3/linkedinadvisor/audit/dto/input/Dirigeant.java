package com.lms3.linkedinadvisor.audit.dto.input;

import java.util.List;

public record Dirigeant(
        boolean present,
        String nomComplet,
        String urlLinkedin,
        Image photo,
        Image banniere,
        String titre,
        String resume,
        List<Experience> experiences,
        List<String> competences,
        String nombreRelations,
        Integer nombreAbonnes,
        List<Publication> publications
) {}
