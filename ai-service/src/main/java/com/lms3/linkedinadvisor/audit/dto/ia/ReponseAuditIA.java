package com.lms3.linkedinadvisor.audit.dto.ia;

import java.util.List;

public record ReponseAuditIA(
        List<EvaluationIA> evaluations,
        List<String> pointsForts,
        List<String> pointsFaibles,
        List<RecommandationIA> recommandations,
        String synthese
) {}
