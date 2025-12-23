package com.spring.userservice.DTOs;

import lombok.Getter;
import lombok.Setter;

import java.time.LocalDateTime;
import java.time.OffsetDateTime;
import java.util.List;

@Getter
@Setter
public class BookingDTO {
    private String id;
    private Long totalPrice;
    private String movieTitle;
    private String cinemaName;
    private String auditoriumName;
    private OffsetDateTime startTime;
    private OffsetDateTime endTime;
    private LocalDateTime createdAt;
    private List<TicketDTO> tickets;

    public BookingDTO(
            String id,
            Long totalPrice,
            String movieTitle,
            String cinemaName,
            String auditoriumName,
            OffsetDateTime startTime,
            OffsetDateTime endTime,
            LocalDateTime createdAt) {
        this.id = id;
        this.totalPrice = totalPrice;
        this.movieTitle = movieTitle;
        this.cinemaName = cinemaName;
        this.auditoriumName = auditoriumName;
        this.startTime = startTime;
        this.endTime = endTime;
        this.createdAt = createdAt;
    }
}
