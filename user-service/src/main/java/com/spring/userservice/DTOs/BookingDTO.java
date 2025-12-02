package com.spring.userservice.DTOs;

import lombok.Builder;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@Builder
public class BookingDTO {
    private Long id;
    // Todo: Detail screening field

    private Long totalAmount;
    private String status;
    private LocalDateTime createdAt;
}
