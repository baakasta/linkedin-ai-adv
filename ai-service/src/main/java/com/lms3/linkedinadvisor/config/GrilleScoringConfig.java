package com.lms3.linkedinadvisor.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

import java.util.List;
import java.util.Optional;

@Configuration
@ConfigurationProperties(prefix = "grille")
public class GrilleScoringConfig {
    private String version;
    private int scoreMax;
    private List<Categorie> categories;

    public String getVersion(){ return version; }
    public void setVersion(String version){ this.version = version; }

    public int getScoreMax(){ return scoreMax; }
    public void setScoreMax(int scoreMax){ this.scoreMax = scoreMax; }

    public List<Categorie> getCategories(){ return categories; }
    public void setCategories(List<Categorie> categories){ this.categories = categories; }


    public int getNoteMax(String critereCode){
        return categories.stream()
                .flatMap(cat -> cat.getCriteres().stream())
                .filter(c -> c.getCode().equals(critereCode))
                .map(Critere::getNoteMax)
                .findFirst()
                .orElseThrow(() ->
                        new IllegalArgumentException("Critère inconnu dans la grille : " + critereCode));
    }

    public Optional<Categorie> getCategorieDuCritere(String critereCode) {
        return categories.stream()
                .filter(cat -> cat.getCriteres().stream()
                        .anyMatch(c -> c.getCode().equals(critereCode)))
                .findFirst();
    }

    // ============================================================
    // Sous-classes (structure du YAML)
    // ============================================================

    public static class Categorie{
        private String code;
        private String libelle;
        private int poids;
        private List<Critere> criteres;

        public String getCode() { return code; }
        public void setCode(String code) { this.code = code; }

        public String getLibelle() { return libelle; }
        public void setLibelle(String libelle) { this.libelle = libelle; }

        public int getPoids() { return poids; }
        public void setPoids(int poids) { this.poids = poids; }

        public List<Critere> getCriteres() { return criteres; }
        public void setCriteres(List<Critere> criteres) { this.criteres = criteres; }
    }

    public static class Critere {
        private String code;
        private String libelle;
        private int noteMax;
        private String methode;   // "regles" | "ia"

        public String getCode() { return code; }
        public void setCode(String code) { this.code = code; }

        public String getLibelle() { return libelle; }
        public void setLibelle(String libelle) { this.libelle = libelle; }

        public int getNoteMax() { return noteMax; }
        public void setNoteMax(int noteMax) { this.noteMax = noteMax; }

        public String getMethode() { return methode; }
        public void setMethode(String methode) { this.methode = methode; }
    }

}
