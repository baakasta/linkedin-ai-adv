package com.lms3.linkedinadvisor.generation.dto.input;

import com.lms3.linkedinadvisor.optimisation.dto.input.ContexteEntreprise;

public record DemandeGeneration(
        String typeContenu,          // publication, carrousel, annonce_recrutement,
        // temoignage_client, etude_de_cas,
        // publication_rh, publication_dirigeant, actualite
        Brief brief,
        ContexteEntreprise contexteEntreprise
) {}
