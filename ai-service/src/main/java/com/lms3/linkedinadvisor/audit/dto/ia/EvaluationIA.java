package com.lms3.linkedinadvisor.audit.dto.ia;

public record EvaluationIA(
        String categorie,
        String critere,
        String niveau,        // "0".."3" OU "non_evaluable"
        String preuve,
        String justification
) {
    /** true si le critère a une note numérique ; false si "non_evaluable". */
    public boolean estEvaluable() {
        return niveau != null && !niveau.equalsIgnoreCase("non_evaluable");
    }

    /**
     * Retourne la note numérique (0..3).
     * À n'appeler que si estEvaluable() == true.
     * Renvoie -1 si le niveau n'est pas un entier valide (sécurité).
     */
    public int niveauNumerique() {
        if (!estEvaluable()) {
            return -1;
        }
        try {
            return Integer.parseInt(niveau.trim());
        } catch (NumberFormatException e) {
            return -1;
        }
    }
}
