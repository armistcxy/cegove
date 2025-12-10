package com.spring.cinemaservice.DTOs;

import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class AuditoriumResponse {
    private Long id;
    private String name;
    private String pattern;
}
