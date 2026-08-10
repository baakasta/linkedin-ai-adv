package com.lms3.linkedinadvisor.generation.service;

import com.fasterxml.jackson.core.json.JsonReadFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.lms3.linkedinadvisor.generation.dto.input.DemandeGeneration;
import com.lms3.linkedinadvisor.generation.dto.output.ResultatGeneration;
import com.lms3.linkedinadvisor.generation.dto.output.VarianteContenu;
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
 * Module GENERATION : produit du contenu LinkedIn a partir d'un brief.
 * Pas de score. Le LLM genere directement des variantes publiables.
 *
 * Robustesse (architecture "le LLM produit, le backend garantit") :
 *   1. Parsing TOLERANT : le LLM met parfois des sauts de ligne bruts dans
 *      les textes longs, ce qui casse le JSON strict. On recupere le texte
 *      brut (.content()) et on parse avec un mapper qui accepte ces sauts
 *      de ligne (ALLOW_UNESCAPED_CONTROL_CHARS).
 *   2. GARDE-FOU CHIFFRES : tout chiffre absent du brief est remplace par
 *      [chiffre a completer] (VerificateurChiffres).
 *   3. EXTRACTION DES MARQUEURS : le LLM met les marqueurs [xxx] dans le
 *      texte mais oublie souvent de les lister. On reconstruit la liste
 *      marqueurs_a_completer directement depuis le texte (fiable a 100%).
 */
@Service
public class GenerationService {

    private final ChatClient chatClient;
    private final ObjectMapper objectMapper;
    private final String systemPrompt;

    // Mapper tolerant : accepte les sauts de ligne bruts dans les chaines JSON.
    private final ObjectMapper mapperTolerant;

    // Detecte tout marqueur entre crochets, ex. [resultat chiffre], [nom du client]
    private static final Pattern MOTIF_MARQUEUR = Pattern.compile("\\[[^\\]]+\\]");

    public GenerationService(
            @Qualifier("chatClientCreatif") ChatClient chatClient,
            ObjectMapper objectMapper,
            @Value("classpath:prompts/generation_system_prompt.txt") Resource promptResource
    ) throws Exception {
        this.chatClient = chatClient;
        this.objectMapper = objectMapper;
        this.systemPrompt = promptResource.getContentAsString(StandardCharsets.UTF_8);

        // Mapper tolerant construit a partir du mapper injecte (garde SNAKE_CASE)
        // + option qui accepte les retours a la ligne non echappes.
        this.mapperTolerant = objectMapper.copy();
        this.mapperTolerant.configure(
                JsonReadFeature.ALLOW_UNESCAPED_CONTROL_CHARS.mappedFeature(), true);
    }

    public ResultatGeneration generer(DemandeGeneration demande) {
        try {
            String demandeJson = objectMapper.writeValueAsString(demande);

            // 1. Generation par le LLM : on recupere le TEXTE BRUT puis on parse
            //    nous-memes avec le mapper tolerant.
            String reponseBrute = chatClient.prompt()
                    .system(systemPrompt)
                    .user(demandeJson)
                    .call()
                    .content();

            String jsonNettoye = nettoyer(reponseBrute);

            ResultatGeneration resultat =
                    mapperTolerant.readValue(jsonNettoye, ResultatGeneration.class);

            // 2. Garde-fou chiffres + extraction des marqueurs
            String source = demandeJson;
            return appliquerGardeFou(resultat, source);

        } catch (Exception ex) {
            throw new GenerationException("Echec de la generation IA", ex);
        }
    }

    /**
     * Retire les eventuelles balises Markdown de bloc de code (```json ... ```)
     * que certains modeles ajoutent autour du JSON.
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
     * Applique le garde-fou chiffres a chaque variante, puis reconstruit la
     * liste des marqueurs a partir du texte reel (le LLM ne la remplit pas
     * de facon fiable).
     */
    private ResultatGeneration appliquerGardeFou(ResultatGeneration resultat, String source) {
        if (resultat.variantes() == null) {
            return resultat;
        }

        List<VarianteContenu> variantesCorrigees = new ArrayList<>();

        for (VarianteContenu v : resultat.variantes()) {
            VerificateurChiffres.ResultatVerification verif =
                    VerificateurChiffres.verifier(v.contenu(), source);

            variantesCorrigees.add(new VarianteContenu(
                    v.angle(),
                    verif.contenuCorrige,   // texte nettoye des chiffres inventes
                    v.hashtags(),
                    v.cta()
            ));
        }

        // Marqueurs extraits directement du texte corrige (fiable a 100%).
        // Cela inclut [chiffre a completer] ajoute par le garde-fou, ainsi que
        // tout marqueur mis par le LLM ([nom du client], [resultat chiffre]...).
        List<String> marqueurs = extraireMarqueurs(variantesCorrigees);

        return new ResultatGeneration(
                resultat.typeContenu(),
                resultat.titreInterne(),
                variantesCorrigees,
                marqueurs
        );
    }

    /**
     * Extrait tous les marqueurs [xxx] presents dans les contenus et les CTA
     * des variantes. Garantit une liste fiable, construite depuis le texte reel.
     */
    private List<String> extraireMarqueurs(List<VarianteContenu> variantes) {
        List<String> marqueurs = new ArrayList<>();
        for (VarianteContenu v : variantes) {
            collecterMarqueurs(v.contenu(), marqueurs);
            collecterMarqueurs(v.cta(), marqueurs);
        }
        return marqueurs.stream().distinct().toList();
    }

    private void collecterMarqueurs(String texte, List<String> cible) {
        if (texte == null) return;
        Matcher m = MOTIF_MARQUEUR.matcher(texte);
        while (m.find()) {
            cible.add(m.group());
        }
    }

    public static class GenerationException extends RuntimeException {
        public GenerationException(String message, Throwable cause) {
            super(message, cause);
        }
    }
}