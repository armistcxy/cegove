package com.spring.cinemaservice.Reposistories;

import com.spring.cinemaservice.Models.ShowtimeSeat;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ShowtimeSeatReposistory extends JpaRepository<ShowtimeSeat, ShowtimeSeat.ShowtimeSeatId> {
    void deleteAllById_ShowtimeId(String showtimeId);
}
