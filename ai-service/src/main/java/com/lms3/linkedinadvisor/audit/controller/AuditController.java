package com.lms3.linkedinadvisor.audit.controller;

import com.lms3.linkedinadvisor.audit.dto.input.DonneesLinkedIn;
import com.lms3.linkedinadvisor.audit.service.AuditService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/audits")
public class AuditController {

    private final AuditService auditService;

    public AuditController(AuditService auditService) {
        this.auditService = auditService;
    }

    @PostMapping
    public ResponseEntity<AuditService.ResultatComplet> auditer(
            @RequestBody DonneesLinkedIn donnees) {

        AuditService.ResultatComplet resultat = auditService.auditer(donnees);
        return ResponseEntity.ok(resultat);
    }
}
