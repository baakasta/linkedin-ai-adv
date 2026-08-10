package com.lms3.linkedinadvisor.generation.dto.input;

import java.util.Map;

public record Brief(
        String sujet,
        String objectif,             // visibilite, recrutement, expertise, prospects
        String messageCle,           // optionnel
        Map<String, Object> elementsFournis   // faits fournis (souples : texte, listes, null)
) {
}
