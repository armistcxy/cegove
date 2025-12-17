package com.spring.userservice.DTOs;

import lombok.Builder;
import lombok.Data;

import java.time.LocalDateTime;
import java.time.OffsetDateTime;
import java.util.List;

@Data
@Builder
public class BookingDTO {
    private String id;
    private Long totalPrice;
    private String movieTitle;
    private String cinemaName;
    private String auditoriumName;
    private OffsetDateTime startTime;
    private OffsetDateTime endTime;
    private List<TicketDTO> tickets;
    private LocalDateTime createdAt;
}
