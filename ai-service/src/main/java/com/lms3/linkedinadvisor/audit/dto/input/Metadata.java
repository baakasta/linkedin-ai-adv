package com.lms3.linkedinadvisor.audit.dto.input;

public record Metadata(
        String extractionId,
        String dateExtraction,
        String source,
        String langue,
        Integer periodeAnalyseJours,
        String versionSchema
) {}
