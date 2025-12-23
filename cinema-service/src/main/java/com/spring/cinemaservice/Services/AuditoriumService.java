package com.spring.cinemaservice.Services;

import com.spring.cinemaservice.DTOs.AuditoriumRequest;
import com.spring.cinemaservice.DTOs.AuditoriumResponse;
import com.spring.cinemaservice.Enums.AuditoriumPattern;
import com.spring.cinemaservice.Models.Auditorium;
import com.spring.cinemaservice.Models.Cinema;
import com.spring.cinemaservice.Models.Seat;
import com.spring.cinemaservice.Models.Showtime;
import com.spring.cinemaservice.Reposistories.AuditoriumReposistory;
import com.spring.cinemaservice.Reposistories.CinemaReposistory;
import com.spring.cinemaservice.Reposistories.SeatReposistory;
import com.spring.cinemaservice.Reposistories.ShowtimeReposistory;
import jakarta.transaction.Transactional;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;

@Service
public class AuditoriumService {
    @Autowired
    private AuditoriumReposistory reposistory;

    @Autowired
    private SeatService seatService;

    @Autowired
    private ShowtimeSeatService showtimeSeatService;

    @Autowired
    private SeatReposistory seatReposistory;

    @Autowired
    private ShowtimeReposistory showtimeReposistory;

    @Autowired
    private CinemaReposistory cinemaReposistory;

    @Transactional
    public void createAuditorium(AuditoriumRequest auditoriumRequest, Long cinemaId) {
        Auditorium auditorium = Auditorium.builder()
                .name(auditoriumRequest.getName())
                .pattern(auditoriumRequest.getPattern())
                .seats(new ArrayList<>())
                .build();
        Cinema cinema = cinemaReposistory.findById(cinemaId)
                .orElseThrow(() -> new UsernameNotFoundException("Cinema not found with id: " + cinemaId));
        auditorium.setCinema(cinema);
        cinema.getAuditoriums().add(auditorium);
        Auditorium savedAuditorium = reposistory.save(auditorium);

        // Generate seating arrangement based on the auditorium pattern
        seatService.saveSeats(savedAuditorium);
    }

    public AuditoriumResponse getAuditoriumById(Long auditoriumId) {
        Auditorium auditorium = reposistory.findById(auditoriumId)
                .orElseThrow(() -> new UsernameNotFoundException("Auditorium not found with id: " + auditoriumId));
        return auditorium.convertToDTO();
    }

    public void deleteAuditorium(Long auditoriumId) {
        Auditorium auditorium = reposistory.findById(auditoriumId)
                .orElseThrow(() -> new UsernameNotFoundException("Auditorium not found with id: " + auditoriumId));
        reposistory.delete(auditorium);
    }

    @Transactional
    public void updateAuditoriumPattern(Long auditoriumId, String newPattern) {
        Auditorium auditorium = reposistory.findById(auditoriumId)
                .orElseThrow(() -> new UsernameNotFoundException("Auditorium not found with id: " + auditoriumId));
        auditorium.setPattern(AuditoriumPattern.valueOf(newPattern));
        Auditorium updatedAuditorium = reposistory.save(auditorium);

        // Update seating arrangement based on the new pattern
        seatService.updateSeats(auditorium);

        List<Seat> updatedSeats = seatReposistory.findAllByAuditorium(updatedAuditorium);

        List<Showtime> showtimes = showtimeReposistory.findUpcomingShowtimesByAuditorium(auditoriumId);

        for (Showtime showtime : showtimes) {
            showtimeSeatService.rebuildShowtimeSeats(showtime, updatedSeats);
        }
    }
}
