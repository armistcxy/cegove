package com.spring.cinemaservice.DTOs;

import lombok.Builder;
import lombok.Data;

import java.math.BigDecimal;

@Data
@Builder
public class CinemaRevenueMonthlyDTO {
    private Long cinemaId;
    private BigDecimal revenue;
}
