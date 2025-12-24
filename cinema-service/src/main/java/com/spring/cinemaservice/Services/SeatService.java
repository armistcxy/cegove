package com.spring.cinemaservice.Services;

import com.spring.cinemaservice.Models.Auditorium;
import com.spring.cinemaservice.Models.Seat;
import com.spring.cinemaservice.Reposistories.SeatReposistory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class SeatService {
    @Autowired
    private SeatReposistory reposistory;

    public void saveSeats(Auditorium auditorium) {
        List<Seat> seats = auditorium.getPattern().generateSeats();
        for (Seat seat : seats) {
            seat.setAuditorium(auditorium);
            auditorium.getSeats().add(seat);
        }
        reposistory.saveAll(seats);
    }

    public List<Seat> updateSeats(Auditorium auditorium) {
        // Remove existing seats
        reposistory.deleteAllByAuditorium(auditorium);

        // Generate new seating arrangement based on the updated pattern
        List<Seat> newSeats = auditorium.getPattern().generateSeats();
        for (Seat seat : newSeats) {
            seat.setAuditorium(auditorium);
            auditorium.getSeats().add(seat);
        }
        return reposistory.saveAll(newSeats);
    }
}
