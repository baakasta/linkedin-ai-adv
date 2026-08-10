package com.lms3.linkedinadvisor.audit.service;

import com.lms3.linkedinadvisor.audit.dto.input.DonneesLinkedIn;
import com.lms3.linkedinadvisor.audit.dto.ia.ReponseAuditIA;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.ai.chat.client.ChatClient;
import org.springframework.beans.factory.annotation.Qualifier;   // AJOUT
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.Resource;
import org.springframework.stereotype.Service;

import java.nio.charset.StandardCharsets;

@Service
public class AiScoringService {

    private final ChatClient chatClient;
    private final ObjectMapper objectMapper;
    private final String systemPrompt;
    // plus de champ temperature

    public AiScoringService(
            @Qualifier("chatClientPrecis") ChatClient chatClient,   // AJOUT du Qualifier
            ObjectMapper objectMapper,
            @Value("classpath:prompts/audit_system_prompt.txt") Resource promptResource
            // plus de paramètre temperature
    ) throws Exception {
        this.chatClient = chatClient;
        this.objectMapper = objectMapper;
        this.systemPrompt = promptResource.getContentAsString(StandardCharsets.UTF_8);
    }

    public ReponseAuditIA evaluer(DonneesLinkedIn donnees) {
        try {
            String donneesJson = objectMapper.writeValueAsString(donnees);
            return chatClient.prompt()
                    .system(systemPrompt)
                    .user(donneesJson)
                    .call()
                    .entity(ReponseAuditIA.class);
        } catch (Exception ex) {
            throw new AuditIAException("Echec de l'evaluation IA de l'audit", ex);
        }
    }

    public static class AuditIAException extends RuntimeException {
        public AuditIAException(String message, Throwable cause) {
            super(message, cause);
        }
    }
}