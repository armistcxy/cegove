package com.spring.cinemaservice.Services;

import com.spring.cinemaservice.Models.Seat;
import com.spring.cinemaservice.Models.Showtime;
import com.spring.cinemaservice.Models.ShowtimeSeat;
import com.spring.cinemaservice.Reposistories.ShowtimeSeatReposistory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class ShowtimeSeatService {
    @Autowired
    private ShowtimeSeatReposistory reposistory;

    public void rebuildShowtimeSeats(Showtime showtime, List<Seat> seats) {

        // Xóa toàn bộ showtime_seats cũ
        reposistory.deleteAllById_ShowtimeId(showtime.getId());

        // Tạo lại showtime_seats mới
        List<ShowtimeSeat> newShowtimeSeats = seats.stream()
                .map(seat -> ShowtimeSeat.builder()
                        .id(new ShowtimeSeat.ShowtimeSeatId(showtime.getId(), seat.getId()))
                        .status(0)
                        .price(showtime.getBasePrice())
                        .build())
                .toList();

        reposistory.saveAll(newShowtimeSeats);
    }
}
