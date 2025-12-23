package com.spring.userservice.Reposistories;

import com.spring.userservice.DTOs.BookingDTO;
import com.spring.userservice.DTOs.TicketDTO;
import com.spring.userservice.Models.Booking;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;

public interface BookingReposistory extends JpaRepository<Booking, String> {
    @Query("""
SELECT new com.spring.userservice.DTOs.BookingDTO(
    b.id,
    b.totalPrice,
    MIN(t.movieTitle),
    MIN(t.cinemaName),
    MIN(t.auditoriumName),
    s.startTime,
    s.endTime,
    b.createdAt
)
FROM Booking b
JOIN b.tickets t
JOIN b.showtime s
WHERE b.user.id = :userId
GROUP BY b.id, b.totalPrice, s.startTime, s.endTime, b.createdAt
ORDER BY b.createdAt DESC
""")
    List<BookingDTO> findBookingDTOByUserId(@Param("userId") Long userId);


    @Query("""
SELECT new com.spring.userservice.DTOs.TicketDTO(
    t.id,
    t.booking.id,
    t.seatNumber,
    t.price
)
FROM Ticket t
WHERE t.booking.id IN :bookingIds
""")
    List<TicketDTO> findTicketsByBookingIds(@Param("bookingIds") List<String> bookingIds);

}