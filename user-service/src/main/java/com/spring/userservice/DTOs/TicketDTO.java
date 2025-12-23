package com.spring.userservice.DTOs;

import lombok.Builder;
import lombok.Data;

import java.math.BigDecimal;

@Data
@Builder
public class TicketDTO {
    private String id;
    private String bookingId;
    private String seatNumber;
    private BigDecimal price;
}
