package com.spring.cinemaservice.Reposistories;

import com.spring.cinemaservice.DTOs.CinemaRevenueMonthlyDTO;
import com.spring.cinemaservice.Models.Booking;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.OffsetDateTime;
import java.util.List;

@Repository
public interface BookingReposistory extends JpaRepository<Booking, String> {
    @Query("""
        SELECT new com.spring.cinemaservice.DTOs.CinemaRevenueMonthlyDTO(
            :cinemaId,
            COALESCE(SUM(b.totalPrice), 0)
        )
        FROM Booking b
        JOIN Showtime s ON b.showtimeId = s.id
        WHERE s.cinemaId = :cinemaId
          AND b.status = 'CONFIRMED'
          AND s.startTime BETWEEN :startDate AND :endDate
    """)
    List<CinemaRevenueMonthlyDTO> getCinemaRevenueByMonth(
            @Param("cinemaId") Long cinemaId,
            @Param("startDate") OffsetDateTime startDate,
            @Param("endDate") OffsetDateTime endDate
    );
}
