package com.spring.cinemaservice.Services;

import com.spring.cinemaservice.DTOs.AuditoriumRequest;
import com.spring.cinemaservice.DTOs.AuditoriumResponse;
import com.spring.cinemaservice.DTOs.CinemaRequest;
import com.spring.cinemaservice.DTOs.CinemaResponse;
import com.spring.cinemaservice.Models.Auditorium;
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
    private ImageUploadClient imageUploadClient;

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

    public void deleteCinema(long id) {
        Cinema cinema = reposistory.findById(id)
                .orElseThrow(() -> new UsernameNotFoundException("Do not have cinema with id:" + id));
        reposistory.delete(cinema);
    }

    public void updateCinema(CinemaRequest cinemaRequest, long id) {
        Cinema cinema = reposistory.findById(id)
                .orElseThrow(() -> new UsernameNotFoundException("Do not have cinema with id:" + id));

        if (cinemaRequest.getName() != null) {
            cinema.setName(cinemaRequest.getName());
        }

        if (cinemaRequest.getAddress() != null) {
            cinema.setAddress(cinemaRequest.getAddress());
        }

        if (cinemaRequest.getDistrict() != null) {
            cinema.setDistrict(cinemaRequest.getDistrict());
        }

        if (cinemaRequest.getCity() != null) {
            cinema.setCity(cinemaRequest.getCity());
        }

        if (cinemaRequest.getPhone() != null) {
            cinema.setPhone(cinemaRequest.getPhone());
        }

        // Handle image uploads
        if (cinemaRequest.getImages() != null && !cinemaRequest.getImages().isEmpty()) {
            List<String> newImageUrls = new ArrayList<>();
            for (MultipartFile image : cinemaRequest.getImages()) {
                String imageUrl = imageUploadClient.uploadImage(image);
                newImageUrls.add(imageUrl);
            }
            cinema.setImages(newImageUrls);
        }

        reposistory.save(cinema);
    }

    public AuditoriumResponse getAuditoriumsByCinemaId(Long cinemaId) {
        Cinema cinema = reposistory.findById(cinemaId)
                .orElseThrow(() -> new UsernameNotFoundException("Cinema not found with id: " + cinemaId));
        return cinema.getAuditoriums().stream()
                .map(Auditorium::convertToDTO)
                .findFirst()
                .orElseThrow(() -> new UsernameNotFoundException("No auditoriums found for cinema with id: " + cinemaId));
    }
}
