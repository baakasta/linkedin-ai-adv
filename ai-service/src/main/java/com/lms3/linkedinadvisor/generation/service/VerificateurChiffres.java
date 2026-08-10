package com.lms3.linkedinadvisor.generation.service;

import java.util.*;
import java.util.regex.*;

/**
 * Garde-fou de vérification factuelle pour le contenu généré.
 *
 * Principe (cohérent avec le reste de l'architecture : le LLM produit,
 * le backend valide) : le prompt réduit fortement l'invention de chiffres,
 * mais ne la garantit pas à 100 %. Cette classe scanne le contenu généré
 * et neutralise tout chiffre / pourcentage / durée / montant qui n'est pas
 * présent dans le brief ou le contexte fourni.
 *
 * Un chiffre non justifié est remplacé par un marqueur [chiffre à compléter]
 * plutôt que laissé tel quel : l'utilisateur voit alors qu'il doit fournir
 * la vraie valeur, au lieu de publier une statistique inventée.
 */
public class VerificateurChiffres {

    // Détecte : pourcentages (80 %, 80%), nombres avec unité ou séparateurs
    // (48h, 3 000, 1.5M), et nombres isolés de 2 chiffres ou plus.
    private static final Pattern MOTIF_CHIFFRE =
            Pattern.compile("\\b\\d[\\d\\s.,]*\\s*(%|h|heures?|jours?|k€|€|M€|millions?|milliers?)?\\b",
                    Pattern.CASE_INSENSITIVE);

    /**
     * @param contenu    le texte généré par le LLM
     * @param sourceBrief la concaténation du brief + contexte (le texte d'entrée)
     * @return le contenu nettoyé, avec les chiffres non justifiés remplacés
     */
    public static ResultatVerification verifier(String contenu, String sourceBrief) {
        Matcher m = MOTIF_CHIFFRE.matcher(contenu);
        StringBuffer sb = new StringBuffer();
        List<String> chiffresNeutralises = new ArrayList<>();

        // Normalisation de la source pour la comparaison (on retire les espaces
        // internes des nombres pour comparer "3 000" et "3000").
        String sourceNormalisee = normaliser(sourceBrief);

        while (m.find()) {
            String chiffreTrouve = m.group().trim();

            // On ignore les "chiffres" vides ou réduits à une unité seule.
            if (!chiffreTrouve.matches(".*\\d.*")) {
                m.appendReplacement(sb, Matcher.quoteReplacement(m.group()));
                continue;
            }

            String chiffreNormalise = normaliser(chiffreTrouve);

            if (sourceNormalisee.contains(chiffreNormalise)) {
                // Le chiffre figure dans le brief : autorisé, on le garde.
                m.appendReplacement(sb, Matcher.quoteReplacement(m.group()));
            } else {
                // Chiffre absent du brief : inventé par le modèle -> neutralisé.
                chiffresNeutralises.add(chiffreTrouve);
                m.appendReplacement(sb, Matcher.quoteReplacement("[chiffre à compléter]"));
            }
        }
        m.appendTail(sb);

        return new ResultatVerification(sb.toString(), chiffresNeutralises);
    }

    private static String normaliser(String s) {
        // minuscules + suppression des espaces à l'intérieur des nombres
        return s.toLowerCase().replaceAll("(?<=\\d)\\s+(?=\\d)", "");
    }

    /** Résultat : le contenu corrigé + la liste des chiffres qui ont été retirés. */
    public static class ResultatVerification {
        public final String contenuCorrige;
        public final List<String> chiffresNeutralises;

        public ResultatVerification(String contenuCorrige, List<String> chiffresNeutralises) {
            this.contenuCorrige = contenuCorrige;
            this.chiffresNeutralises = chiffresNeutralises;
        }

        public boolean aDetecteDesInventions() {
            return !chiffresNeutralises.isEmpty();
        }
    }

    // Démonstration
    public static void main(String[] args) {
        String brief = "beaucoup d'industriels subissent des arrêts non planifiés ; "
                + "approche : capteurs connectés et analyse temps réel.";

        String contenuGenere =
                "80 % des pannes en industrie sont précédées de signaux faibles. "
                        + "Nos capteurs détectent les anomalies en temps réel pour éviter "
                        + "les arrêts non planifiés.";

        ResultatVerification res = verifier(contenuGenere, brief);

        System.out.println("Contenu corrigé :");
        System.out.println(res.contenuCorrige);
        System.out.println();
        System.out.println("Chiffres neutralisés : " + res.chiffresNeutralises);
        System.out.println("Invention détectée ? " + res.aDetecteDesInventions());
    }
}