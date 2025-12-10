package com.spring.cinemaservice.Services;

import com.spring.cinemaservice.DTOs.AuditoriumRequest;
import com.spring.cinemaservice.DTOs.CinemaRequest;
import com.spring.cinemaservice.DTOs.CinemaResponse;
import com.spring.cinemaservice.Models.Cinema;
import com.spring.cinemaservice.Reposistories.CinemaReposistory;
import jakarta.transaction.Transactional;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.util.ArrayList;
import java.util.List;

@Service
public class CinemaService {
    @Autowired
    private CinemaReposistory reposistory;

    @Autowired
    private AuditoriumService auditoriumService;

    @Autowired
    private ImageUploadClient imageUploadClient;

    @Transactional
    public void createCinema(CinemaRequest cinemaRequest) {
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
                String imageUrl = imageUploadClient.uploadImage(image);
                cinema.getImages().add(imageUrl);
            }
        }

        Cinema savedCinema = reposistory.save(cinema);

        // Create auditoriums
        if (cinemaRequest.getAuditoriumList() != null) {
            for (AuditoriumRequest auditoriumRequest : cinemaRequest.getAuditoriumList()) {
                auditoriumService.createAuditorium(auditoriumRequest, savedCinema.getId());
            }
        }
    }

    public CinemaResponse getCinema(long id) {
        Cinema cinema = reposistory.findById(id)
                .orElseThrow(() -> new UsernameNotFoundException("Do not have cinema with id:" + id));
        return cinema.convertToDTO();
    }

    public List<CinemaResponse> getAllCinemas() {
        List<Cinema> cinemas = reposistory.findAll();
        return cinemas.stream()
                .map(Cinema::convertToDTO)
                .toList();
    }

    public List<CinemaResponse> getCinemasByCity(String city) {
        List<Cinema> cinemas = reposistory.findByCityIgnoreCase(city);
        return cinemas.stream()
                .map(Cinema::convertToDTO)
                .toList();
    }
}
