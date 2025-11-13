package com.spring.cinemaservice.Services;

import com.spring.cinemaservice.DTOs.AuditoriumDTO;
import com.spring.cinemaservice.DTOs.CinemaRequest;
import com.spring.cinemaservice.DTOs.CinemaResponse;
import com.spring.cinemaservice.Mapper.CinemaMapper;
import com.spring.cinemaservice.Models.Cinema;
import com.spring.cinemaservice.Reposistories.CinemaReposistory;
import jakarta.transaction.Transactional;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

@Service
public class CinemaService {
    @Autowired
    private CinemaReposistory reposistory;

//    @Autowired
//    private CinemaMapper mapper;

    @Autowired
    private AuditoriumService auditoriumService;

    @Autowired
    private ImageService imageService;

    @Transactional
    public void createCinema(CinemaRequest cinemaRequest) throws IOException {
        Cinema cinema = Cinema.builder()
                .name(cinemaRequest.getName())
                .address(cinemaRequest.getAddress())
                .district(cinemaRequest.getDistrict())
                .city(cinemaRequest.getCity())
                .phone(cinemaRequest.getPhone())
                .build();

        // Handle image uploads
        cinema.setImages(new ArrayList<>());
        if (cinemaRequest.getImages() != null) {
            for (MultipartFile image : cinemaRequest.getImages()) {
                String imageUrl = imageService.uploadImage(image);
                cinema.getImages().add(imageUrl);
            }
        }


        Cinema savedCinema = reposistory.save(cinema);

        // Create auditoriums
        if (cinemaRequest.getAuditoriumList() != null) {
            for (AuditoriumDTO auditoriumDTO : cinemaRequest.getAuditoriumList()) {
                auditoriumService.createAuditorium(auditoriumDTO, savedCinema.getId());
            }
        }
    }

    public CinemaResponse getCinema(long id) {
        Cinema cinema = reposistory.findById(id)
                .orElseThrow(() -> new RuntimeException("Do not have cinema with id:" + id));
        return CinemaResponse.builder()
                .name(cinema.getName())
                .address(cinema.getAddress())
                .district(cinema.getDistrict())
                .city(cinema.getCity())
                .phone(cinema.getPhone())
                .build();
    }
}
