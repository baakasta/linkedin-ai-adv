package com.lms3.linkedinadvisor.audit.dto.input;

import java.util.List;

public record Publication(
        String id,
        String date,
        String type,
        String contenu,
        List<String> hashtags,
        Integer reactions,
        Integer commentaires,
        Integer partages
) {}
