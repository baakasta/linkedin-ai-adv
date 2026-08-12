package com.lms3.linkedinadvisor.optimisation.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.json.JsonReadFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.lms3.linkedinadvisor.optimisation.dto.input.DemandeOptimisation;
import com.lms3.linkedinadvisor.optimisation.dto.output.ResultatOptimisation;
import com.lms3.linkedinadvisor.optimisation.dto.output.VarianteOptimisee;
import org.springframework.ai.chat.client.ChatClient;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.Resource;
import org.springframework.stereotype.Service;

import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Module OPTIMISATION : reecrit un contenu a partir d'une recommandation
 * d'audit. Pas de score.
 *
 * Robustesse (architecture "le LLM produit, le backend garantit") :
 *   1. Parsing TOLERANT : accepte les sauts de ligne bruts dans les textes
 *      longs (description, resume dirigeant, publication), qui casseraient
 *      le JSON strict.
 *   2. EXTRACTION DES MARQUEURS : reconstruit la liste marqueurs_a_completer
 *      directement depuis le texte (le LLM ne la remplit pas de facon fiable).
 *
 * Pas de garde-fou chiffres ici (specifique a la generation).
 */
@Service
public class OptimisationService {

    private final ChatClient chatClient;
    private final ObjectMapper objectMapper;
    private final String systemPrompt;

    // Mapper tolerant : accepte les sauts de ligne bruts dans les chaines JSON.
    private final ObjectMapper mapperTolerant;

    // Nombre maximal d'appels LLM pour une meme demande (le JSON peut etre malforme).
    private static final int MAX_TENTATIVES = 2;

    // Detecte tout marqueur entre crochets, ex. [chiffre a completer], [nom du client]
    private static final Pattern MOTIF_MARQUEUR = Pattern.compile("\\[[^\\]]+\\]");

    public OptimisationService(
            @Qualifier("chatClientPrecis") ChatClient chatClient,
            ObjectMapper objectMapper,
            @Value("classpath:prompts/optimisation_system_prompt.txt") Resource promptResource
    ) throws Exception {
        this.chatClient = chatClient;
        this.objectMapper = objectMapper;
        this.systemPrompt = promptResource.getContentAsString(StandardCharsets.UTF_8);

        this.mapperTolerant = objectMapper.copy();
        this.mapperTolerant.configure(
                JsonReadFeature.ALLOW_UNESCAPED_CONTROL_CHARS.mappedFeature(), true);
    }

    public ResultatOptimisation optimiser(DemandeOptimisation demande) {
        try {
            String demandeJson = objectMapper.writeValueAsString(demande);

            JsonProcessingException derniereErreur = null;

            // Le LLM peut produire un JSON malforme : on relance la demande un
            // nombre limite de fois avant d'abandonner.
            for (int tentative = 1; tentative <= MAX_TENTATIVES; tentative++) {
                String reponseBrute = chatClient.prompt()
                        .system(systemPrompt)
                        .user(demandeJson)
                        .call()
                        .content();

                String jsonNettoye = nettoyer(reponseBrute);

                ResultatOptimisation resultat = parseResultat(jsonNettoye);
                if (resultat != null) {
                    // Reconstruire la liste des marqueurs depuis le texte reel.
                    return corrigerMarqueurs(resultat);
                }

                try {
                    mapperTolerant.readTree(jsonNettoye);
                } catch (JsonProcessingException ex) {
                    derniereErreur = ex;
                }
            }

            throw new OptimisationException(
                    "Echec de l'optimisation IA : JSON LLM invalide apres "
                            + MAX_TENTATIVES + " tentatives",
                    derniereErreur);

        } catch (Exception ex) {
            throw new OptimisationException("Echec de l'optimisation IA", ex);
        }
    }

    /**
     * Parse le JSON du LLM de facon robuste :
     *   1. essai direct ;
     *   2. si echec, normalisation : un champ attendu en String qui arrive en
     *      objet ({...}) est converti en texte.
     * Retourne null si aucune forme n'est exploitable.
     */
    private ResultatOptimisation parseResultat(String jsonNettoye) {
        try {
            return mapperTolerant.readValue(jsonNettoye, ResultatOptimisation.class);
        } catch (JsonProcessingException ex) {
            return parseResultatNormalise(jsonNettoye);
        }
    }

    /**
     * Normalise les formes les plus courantes de JSON LLM malforme : un objet
     * dans un champ attendu en String (ex. "contenu": {"texte": "..."}) est
     * converti en texte avant re-deserialisation.
     */
    private ResultatOptimisation parseResultatNormalise(String jsonNettoye) {
        try {
            JsonNode racine = mapperTolerant.readTree(jsonNettoye);
            if (racine == null || !racine.isObject()) {
                return null;
            }
            JsonNode variantes = racine.path("variantes");
            if (variantes.isArray()) {
                for (JsonNode variante : variantes) {
                    normaliserChampTexte(variante, "contenu");
                    normaliserChampTexte(variante, "angle");
                    normaliserChampTexte(variante, "explication");
                }
            }
            return mapperTolerant.convertValue(racine, ResultatOptimisation.class);
        } catch (JsonProcessingException | IllegalArgumentException ex) {
            return null;
        }
    }

    /**
     * Si la valeur du champ attendu en String est un objet, prend la valeur de
     * "texte" si presente, sinon serialise l'objet en JSON.
     */
    private void normaliserChampTexte(JsonNode noeud, String champ) {
        if (!(noeud instanceof ObjectNode objectNode)) {
            return;
        }
        JsonNode valeur = objectNode.get(champ);
        if (valeur != null && valeur.isObject()) {
            String texte = valeur.path("texte").asText(null);
            objectNode.put(champ, texte != null ? texte : valeur.toString());
        }
    }

    /**
     * Retire les eventuelles balises Markdown de bloc de code (```json ... ```).
     */
    private String nettoyer(String texte) {
        if (texte == null) return "";
        String t = texte.trim();
        if (t.startsWith("```")) {
            int debut = t.indexOf('\n');
            if (debut != -1) {
                t = t.substring(debut + 1);
            }
            if (t.endsWith("```")) {
                t = t.substring(0, t.length() - 3);
            }
        }
        return t.trim();
    }

    /**
     * Reconstruit marqueurs_a_completer a partir des [xxx] presents dans le
     * texte des variantes (le LLM ne remplit pas cette liste de facon fiable).
     */
    private ResultatOptimisation corrigerMarqueurs(ResultatOptimisation resultat) {
        if (resultat.variantes() == null) {
            return resultat;
        }

        List<String> marqueurs = new ArrayList<>();
        for (VarianteOptimisee v : resultat.variantes()) {
            collecterMarqueurs(v.contenu(), marqueurs);
        }
        List<String> marqueursUniques = marqueurs.stream().distinct().toList();

        return new ResultatOptimisation(
                resultat.typeElement(),
                resultat.contenuOriginal(),
                resultat.faiblessesCorrigees(),
                resultat.variantes(),
                marqueursUniques,               // liste reconstruite
                resultat.ameliorationsApportees(),
                resultat.varianteRecommandee()
        );
    }

    private void collecterMarqueurs(String texte, List<String> cible) {
        if (texte == null) return;
        Matcher m = MOTIF_MARQUEUR.matcher(texte);
        while (m.find()) {
            cible.add(m.group());
        }
    }

    public static class OptimisationException extends RuntimeException {
        public OptimisationException(String message, Throwable cause) {
            super(message, cause);
        }
    }
}