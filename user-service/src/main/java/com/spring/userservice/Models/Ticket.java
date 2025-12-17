package com.spring.userservice.Models;

import com.spring.userservice.DTOs.TicketDTO;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.math.BigDecimal;

@Entity
@Table(name = "tickets")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class Ticket {
    @Id
    private String id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "booking_id")
    private Booking booking;

    private String movieTitle;
    private String cinemaName;
    private String auditoriumName;
    private String seatNumber;

    @Column(precision = 10, scale = 2)
    private BigDecimal price;

    public TicketDTO convertToDTO() {
        return TicketDTO.builder()
                .id(this.id)
                .seatNumber(this.seatNumber)
                .price(this.price)
                .build();
    }
}
