package com.spring.userservice.Models;

import com.spring.userservice.DTOs.BookingDTO;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.LocalDateTime;

@Entity
@Table(name = "bookings")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class Booking {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id")
    private User user;

    private Long screeningId;
    private Long totalAmount;
    private String status;
    private final LocalDateTime createdAt = LocalDateTime.now();

    public BookingDTO convertToDTO() {
        return BookingDTO.builder()
                .id(id)
                .totalAmount(totalAmount)
                .status(status)
                .createdAt(createdAt).build();
    }
}
