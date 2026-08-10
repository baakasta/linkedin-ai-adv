package com.lms3.linkedinadvisor.audit.model;

public enum MethodeEvaluation {
    REGLES,     // critère calculé par le backend (présence, métriques)
    IA          // critère évalué par le LLM Judge
}
