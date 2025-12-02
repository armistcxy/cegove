package com.spring.cinemaservice.DTOs;

import com.spring.cinemaservice.Enums.AuditoriumPattern;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class AuditoriumDTO {
    private String name;
    private AuditoriumPattern pattern;
}
