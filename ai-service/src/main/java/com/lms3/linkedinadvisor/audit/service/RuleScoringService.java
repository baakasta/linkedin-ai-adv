package com.lms3.linkedinadvisor.audit.service;

import com.lms3.linkedinadvisor.audit.dto.input.*;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
public class RuleScoringService {

    public Map<String, Integer> calculer(DonneesLinkedIn donnees) {
        Map<String,Integer> notes = new HashMap<>();

        Entreprise e = donnees.entreprise();

        // ---------- EXISTENCE entreprise (max 1) ----------
        notes.put("logo", present(e.logo()));
        notes.put("banniere", present(e.banniere()));
        notes.put("cta", (e.cta() != null && e.cta().present()) ? 1 : 0);
        notes.put("coordonnees", coordonneesPresentes(e.coordonnees()) ? 1 : 0);

        // ---------- METRIQUES entreprise (max 2) ----------
        int periodeJours = (donnees.metadata() != null
                && donnees.metadata().periodeAnalyseJours() != null)
                ? donnees.metadata().periodeAnalyseJours() : 90;

        notes.put("frequence_publication",
                noteFrequence(e.publications(), periodeJours));
        notes.put("engagement",
                noteEngagement(e.publications(), e.nombreAbonnes()));

        // ---------- Criteres dirigeant (existence) ----------
        // Uniquement si le dirigeant est present. Sinon on ne met rien
        // -> non_evaluable pour l'agregateur.
        Dirigeant d = donnees.dirigeant();
        if (d != null && d.present()) {
            notes.put("photo_dirigeant", present(d.photo()));
            notes.put("banniere_dirigeant", present(d.banniere()));
        }

        return notes;
    }

    // ============================================================
    // Helpers d'existence
    // ============================================================
    private int present(Image img) {
        return (img != null && img.present()) ? 1 : 0;
    }

    private boolean coordonneesPresentes(Coordonnees c) {
        if (c == null) return false;
        // Presentes si au moins un moyen de contact est renseigne.
        return notBlank(c.siteWeb()) || notBlank(c.telephone())
                || notBlank(c.email()) || notBlank(c.adresse());
    }

    private boolean notBlank(String s) {
        return s != null && !s.isBlank();
    }

    // ============================================================
    // Metriques (seuils indicatifs, a calibrer)
    // ============================================================

    /**
     * Frequence de publication sur la periode analysee.
     * Seuils (a ajuster a la calibration) :
     *   0 : moins de ~1 publication / mois
     *   1 : environ 1 a 3 publications / mois
     *   2 : plus de ~3 publications / mois (rythme regulier)
     */
    private int noteFrequence(List<Publication> publications, int periodeJours) {
        if (publications == null || publications.isEmpty()) return 0;

        double mois = Math.max(periodeJours / 30.0, 1.0);
        double parMois = publications.size() / mois;

        if (parMois < 1.0) return 0;
        if (parMois <= 3.0) return 1;
        return 2;
    }

    /**
     * Taux d'engagement moyen = (reactions + commentaires + partages) moyens
     * par publication, rapporte au nombre d'abonnes.
     * Seuils (a ajuster a la calibration) :
     *   0 : engagement tres faible ou pas d'abonnes connus
     *   1 : engagement modere
     *   2 : bon engagement
     */
    private int noteEngagement(List<Publication> publications, Integer nombreAbonnes) {
        if (publications == null || publications.isEmpty()) return 0;
        if (nombreAbonnes == null || nombreAbonnes <= 0) return 0;

        double totalInteractions = 0;
        for (Publication p : publications) {
            totalInteractions += valeur(p.reactions())
                    + valeur(p.commentaires())
                    + valeur(p.partages());
        }
        double moyenneParPost = totalInteractions / publications.size();
        double tauxPourcent = (moyenneParPost / nombreAbonnes) * 100.0;

        if (tauxPourcent < 1.0) return 0;
        if (tauxPourcent < 3.0) return 1;
        return 2;
    }

    private int valeur(Integer i) {
        return i != null ? i : 0;
    }

}
