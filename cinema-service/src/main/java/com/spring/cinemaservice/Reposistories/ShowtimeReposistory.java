package com.spring.cinemaservice.Reposistories;

import com.spring.cinemaservice.Models.Showtime;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface ShowtimeReposistory extends JpaRepository<Showtime, String> {
    @Query("""
SELECT s FROM Showtime s
WHERE s.auditoriumId = :auditoriumId
AND s.startTime > CURRENT_TIMESTAMP
""")
    List<Showtime> findUpcomingShowtimesByAuditorium(@Param("auditoriumId") Long auditoriumId);
}
