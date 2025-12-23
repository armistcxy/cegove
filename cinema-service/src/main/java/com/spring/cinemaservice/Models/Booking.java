package com.spring.cinemaservice.Models;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

import java.math.BigDecimal;

@Entity
@Table(name = "bookings")
public class Booking {
    @Id
    private String id;

    private String showtimeId;
    private BigDecimal totalPrice;
    private String status;
}
