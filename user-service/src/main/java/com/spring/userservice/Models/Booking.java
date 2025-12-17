package com.spring.userservice.Models;

import com.spring.userservice.DTOs.BookingDTO;
import jakarta.persistence.CascadeType;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.OneToMany;
import jakarta.persistence.Table;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

@Entity
@Table(name = "bookings")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class Booking {
    @Id
    private String id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id")
    private User user;

    @OneToMany(mappedBy = "booking", fetch = FetchType.LAZY, cascade = CascadeType.ALL)
    private List<Ticket> tickets = new ArrayList<>();

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "showtime_id")
    private Showtime showtime;

    private Long totalPrice;
    private String status;
    private final LocalDateTime createdAt = LocalDateTime.now();

    public BookingDTO convertToDTO() {
        return BookingDTO.builder()
                .id(id)
                .totalPrice(totalPrice)
                .movieTitle((tickets != null && !tickets.isEmpty()) ? tickets.get(0).getMovieTitle() : null)
                .cinemaName((tickets != null && !tickets.isEmpty()) ? tickets.get(0).getCinemaName() : null)
                .auditoriumName(!tickets.isEmpty() ? tickets.get(0).getAuditoriumName() : null)
                .startTime(showtime != null ? showtime.getStartTime() : null)
                .endTime(showtime != null ? showtime.getEndTime() : null)
                .tickets(tickets.stream().map(Ticket::convertToDTO).toList())
                .createdAt(createdAt).build();
    }
}
