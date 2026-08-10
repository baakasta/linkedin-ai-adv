package com.lms3.linkedinadvisor.optimisation.dto.input;

public record DemandeOptimisation(
        String typeElement,          // slogan, description_entreprise, services,
        // cta, mots_cles, hashtags, publication,
        // resume_dirigeant, titre_dirigeant
        String contenuActuel,        // le texte existant a ameliorer (vide si creation)
        ResultatAuditInput resultatAudit,
        ContexteEntreprise contexteEntreprise
) {}
