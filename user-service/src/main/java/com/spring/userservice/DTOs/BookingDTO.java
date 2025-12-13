package com.spring.userservice.DTOs;

import lombok.Builder;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@Builder
public class BookingDTO {
    private String id;
    private Long totalPrice;
    private String status;
    private LocalDateTime createdAt;
}
