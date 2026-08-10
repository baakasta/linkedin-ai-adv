package com.lms3.linkedinadvisor.generation.dto.output;

import java.util.List;

public record VarianteContenu(
        String angle,
        String contenu,
        List<String> hashtags,
        String cta
) {}
