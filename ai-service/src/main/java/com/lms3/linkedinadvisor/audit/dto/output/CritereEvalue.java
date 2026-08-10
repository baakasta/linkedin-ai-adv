package com.lms3.linkedinadvisor.audit.dto.output;

public record CritereEvalue(
        String code,
        String libelle,
        String methode,                  // "regles" | "ia"
        Integer note,                    // null si non_evaluable
        int noteMax,
        boolean nonEvaluable,
        String constat,
        String justificationIa           // présent seulement pour methode = "ia"

) {}
