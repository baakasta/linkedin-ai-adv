package com.lms3.linkedinadvisor.audit.service;

import com.lms3.linkedinadvisor.audit.dto.ia.EvaluationIA;
import com.lms3.linkedinadvisor.audit.dto.ia.ReponseAuditIA;
import com.lms3.linkedinadvisor.audit.dto.input.DonneesLinkedIn;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.Map;

/**
 * Orchestrateur du module audit. C'est lui qui coordonne les trois services :
 *
 *   1. AiScoringService   -> notes des criteres qualitatifs (LLM)
 *   2. RuleScoringService -> notes des criteres deterministes (regles)
 *   3. ScoreAggregator    -> fusionne les notes et calcule le score (70/30)
 *
 * Retourne un objet regroupant la reponse du LLM (evaluations, recommandations,
 * synthese) et le resultat du calcul de score.
 *
 * NB : la construction du DTO de sortie final (ResultatAudit du package output)
 * peut etre ajoutee ici ou dans une classe de mapping dediee. Pour l'instant on
 * renvoie un objet combine simple, suffisant pour tester la chaine complete.
 */
@Service
public class AuditService {
    private final AiScoringService aiScoringService;
    private final RuleScoringService ruleScoringService;
    private final ScoreAggregator scoreAggregator;

    public AuditService(AiScoringService aiScoringService,
                        RuleScoringService ruleScoringService,
                        ScoreAggregator scoreAggregator) {
        this.aiScoringService = aiScoringService;
        this.ruleScoringService = ruleScoringService;
        this.scoreAggregator = scoreAggregator;
    }

    public ResultatComplet auditer(DonneesLinkedIn donnees) {

        // 1. Evaluation qualitative par le LLM
        ReponseAuditIA reponseIA = aiScoringService.evaluer(donnees);

        // 2. Criteres deterministes par les regles
        Map<String, Integer> notes = new HashMap<>(
                ruleScoringService.calculer(donnees));

        // 3. Ajouter les notes du LLM a la map.
        //    Un critere non_evaluable n'est PAS ajoute -> exclu du calcul.
        if (reponseIA.evaluations() != null) {
            for (EvaluationIA ev : reponseIA.evaluations()) {
                if (ev.estEvaluable()) {
                    notes.put(ev.critere(), ev.niveauNumerique());
                }
                // sinon : non_evaluable -> on ne met rien
            }
        }

        // 4. Le dirigeant est-il present ?
        boolean dirigeantPresent =
                donnees.dirigeant() != null && donnees.dirigeant().present();

        // 5. Calcul du score (methode 70/30)
        ScoreAggregator.ResultatScore score =
                scoreAggregator.calculer(notes, dirigeantPresent);

        return new ResultatComplet(score, reponseIA);
    }

    /**
     * Resultat combine : le score calcule + la reponse qualitative du LLM.
     * Le controller pourra le transformer en DTO de sortie (ResultatAudit).
     */
    public record ResultatComplet(
            ScoreAggregator.ResultatScore score,
            ReponseAuditIA analyseIA
    ) {}
}
