package com.spring.authservice.DTOs;

import lombok.Builder;
import lombok.Data;

import java.util.List;

@Data
@Builder
public class MailRequest {
    private List<String> to;
    private String subject;
    private String body;
}