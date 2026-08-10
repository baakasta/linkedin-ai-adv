package com.lms3.linkedinadvisor.optimisation.controller;

import com.lms3.linkedinadvisor.optimisation.dto.input.DemandeOptimisation;
import com.lms3.linkedinadvisor.optimisation.dto.output.ResultatOptimisation;
import com.lms3.linkedinadvisor.optimisation.service.OptimisationService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

/**
 * Point d'entree REST du module optimisation.
 *
 * POST /api/optimisations
 *   corps : DemandeOptimisation (type d'element + contenu actuel + resultat audit)
 *   reponse : ResultatOptimisation (les variantes reecrites)
 */
@RestController
@RequestMapping("/api/optimisations")
public class OptimisationController {

    private final OptimisationService optimisationService;

    public OptimisationController(OptimisationService optimisationService) {
        this.optimisationService = optimisationService;
    }

    @PostMapping
    public ResponseEntity<ResultatOptimisation> optimiser(
            @RequestBody DemandeOptimisation demande) {

        ResultatOptimisation resultat = optimisationService.optimiser(demande);
        return ResponseEntity.ok(resultat);
    }
}