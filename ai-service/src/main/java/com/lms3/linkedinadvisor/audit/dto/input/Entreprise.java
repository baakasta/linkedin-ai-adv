package com.lms3.linkedinadvisor.audit.dto.input;

import java.util.List;

public record Entreprise(
        String nom,
        String urlLinkedin,
        Image logo,
        Image banniere,
        String slogan,
        String description,
        List<String> services,
        Cta cta,
        Coordonnees coordonnees,
        String secteur,
        String taille,
        Integer anneeCreation,
        List<String> specialites,
        Integer nombreAbonnes,
        List<Publication> publications
) {}
