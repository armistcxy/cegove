package com.spring.cinemaservice.Reposistories;

import com.spring.cinemaservice.Models.Auditorium;
import com.spring.cinemaservice.Models.Seat;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface SeatReposistory extends JpaRepository<Seat, Long> {
    void deleteAllByAuditorium(Auditorium auditorium);
    List<Seat> findAllByAuditorium(Auditorium auditorium);
}
