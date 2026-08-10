package com.lms3.linkedinadvisor.audit.model;

public enum CritereCode {
    // Page entreprise
    SLOGAN("slogan", 2),
    DESCRIPTION_ENTREPRISE("description_entreprise", 3),
    SERVICES("services", 2),
    SEO_MOTS_CLES("seo_mots_cles", 2),
    PUBLICATIONS_ENTREPRISE("publications_entreprise", 3),

    // Dirigeant
    TITRE_DIRIGEANT("titre_dirigeant", 2),
    RESUME_DIRIGEANT("resume_dirigeant", 3),
    EXPERIENCE_DIRIGEANT("experience_dirigeant", 2),
    COMPETENCES_DIRIGEANT("competences_dirigeant", 2),
    PUBLICATIONS_DIRIGEANT("publications_dirigeant", 2),

    // Cohérence
    COHERENCE_DIRIGEANT_ENTREPRISE("coherence_dirigeant_entreprise", 2);

    private final String code;
    private final int noteMax;

    CritereCode(String code, int noteMax) {
        this.code = code;
        this.noteMax = noteMax;
    }

    public String getCode() {
        return code;
    }

    public int getNoteMax() {
        return noteMax;
    }

    /** Retrouve un CritereCode à partir de son code JSON. */
    public static CritereCode fromCode(String code) {
        for (CritereCode c : values()) {
            if (c.code.equals(code)) {
                return c;
            }
        }
        throw new IllegalArgumentException("Code de critère inconnu : " + code);
    }
}
