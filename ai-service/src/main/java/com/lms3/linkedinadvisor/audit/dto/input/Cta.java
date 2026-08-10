package com.lms3.linkedinadvisor.audit.dto.input;

public record Cta(
        boolean present,
        String type,
        String url
) {}
