package com.spring.userservice.Services;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.http.client.MultipartBodyBuilder;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.reactive.function.BodyInserters;
import org.springframework.web.reactive.function.client.WebClient;

@Service
public class ImageUploadClient {
    private final WebClient webClient = WebClient.builder()
            .baseUrl("http://localhost:3004")
            .build();

    @Value("${internal.secret.key}")
    private String internalSecretKey;

    public String uploadImage(MultipartFile file) {
        MultipartBodyBuilder builder = new MultipartBodyBuilder();
        builder.part("img", file.getResource())
                .filename(file.getOriginalFilename());

        String imageUrl = webClient.post()
                .uri("/images")
                .contentType(MediaType.MULTIPART_FORM_DATA)
                .header("X-Internal-Secret-key", internalSecretKey)
                .body(BodyInserters.fromMultipartData(builder.build()))
                .retrieve()
                .bodyToMono(String.class)
                .block();

        return imageUrl;
    }
}