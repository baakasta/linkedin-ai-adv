package com.lms3.linkedinadvisor.config;

import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.mistralai.MistralAiChatModel;
import org.springframework.ai.mistralai.MistralAiChatOptions;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class AiConfig {

    // ChatClient à température 0 (audit, optimisation)
    @Bean
    public ChatClient chatClientPrecis(MistralAiChatModel chatModel) {
        return ChatClient.builder(chatModel)
                .defaultOptions(MistralAiChatOptions.builder()
                        .temperature(0.0)
                        .build())
                .build();
    }

    @Bean
    public ChatClient chatClientCreatif(MistralAiChatModel chatModel) {
        return ChatClient.builder(chatModel)
                .defaultOptions(MistralAiChatOptions.builder()
                        .temperature(0.3)
                        .build())
                .build();
    }
}