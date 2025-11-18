package com.spring.cinemaservice.Reposistories;

import com.spring.cinemaservice.Models.Seat;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface SeatReposistory extends JpaRepository<Seat, Long> {
}
