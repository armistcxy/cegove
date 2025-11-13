package com.spring.cinemaservice.Services;

import com.spring.cinemaservice.DTOs.AuditoriumDTO;
import com.spring.cinemaservice.Mapper.AuditoriumMapper;
import com.spring.cinemaservice.Models.Auditorium;
import com.spring.cinemaservice.Reposistories.AuditoriumReposistory;
import jakarta.transaction.Transactional;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class AuditoriumService {
    @Autowired
    private AuditoriumReposistory reposistory;

//    @Autowired
//    private AuditoriumMapper mapper;

    @Autowired
    private SeatService seatService;

    @Transactional
    public void createAuditorium(AuditoriumDTO auditoriumDTO, Long cinemaId) {
        Auditorium auditorium = Auditorium.builder()
                .name(auditoriumDTO.getName())
                .pattern(auditoriumDTO.getPattern())
                .build();
        auditorium.setCinemaId(cinemaId);
        Auditorium savedAuditorium = reposistory.save(auditorium);

        // Generate seating arrangement based on the auditorium pattern
        seatService.saveSeats(savedAuditorium);
    }
}
