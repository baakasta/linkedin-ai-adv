package com.lms3.linkedinadvisor.generation.controller;

import com.lms3.linkedinadvisor.generation.dto.input.DemandeGeneration;
import com.lms3.linkedinadvisor.generation.dto.output.ResultatGeneration;
import com.lms3.linkedinadvisor.generation.service.GenerationService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

/**
 * Point d'entree REST du module generation.
 *
 * POST /api/generations
 *   corps : DemandeGeneration (type de contenu + brief + contexte)
 *   reponse : ResultatGeneration (les variantes de contenu, chiffres verifies)
 */
@RestController
@RequestMapping("/api/generations")
public class GenerationController {

    private final GenerationService generationService;

    public GenerationController(GenerationService generationService) {
        this.generationService = generationService;
    }

    @PostMapping
    public ResponseEntity<ResultatGeneration> generer(
            @RequestBody DemandeGeneration demande) {

        ResultatGeneration resultat = generationService.generer(demande);
        return ResponseEntity.ok(resultat);
    }
}