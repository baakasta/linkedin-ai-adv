package com.lms3.linkedinadvisor.generation.dto.output;

import com.fasterxml.jackson.annotation.JsonAlias;

import java.util.List;

public record ResultatGeneration(
        String typeContenu,
        String titreInterne,
        List<VarianteContenu> variantes,
        @JsonAlias({"marqueurs_acompleter", "marqueursAcompleter"})
        List<String> marqueursACompleter
) {}
