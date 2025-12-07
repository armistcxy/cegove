package com.spring.cinemaservice.Controllers;

import com.spring.cinemaservice.DTOs.AuditoriumDTO;
import com.spring.cinemaservice.DTOs.CinemaRequest;
import com.spring.cinemaservice.DTOs.CinemaResponse;
import com.spring.cinemaservice.Services.AuditoriumService;
import com.spring.cinemaservice.Services.CinemaService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.reactive.function.client.WebClientResponseException;

@RestController
@RequestMapping("/cinemas")
public class CinemaController {
    @Autowired
    private CinemaService service;

    @Autowired
    private AuditoriumService auditoriumService;

    @PreAuthorize("hasAuthority('SUPER_ADMIN')")
    @PostMapping("")
    public ResponseEntity<?> createCinema(@ModelAttribute CinemaRequest req) {
        try {
            service.createCinema(req);
            return ResponseEntity.status(201).body("Create");
        } catch (WebClientResponseException e) {
            return ResponseEntity.status(e.getRawStatusCode()).body(e.getResponseBodyAsString());
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(e.getMessage());
        }
    }

    @PreAuthorize("hasAuthority('SUPER_ADMIN')")
    @PostMapping("/{id}/auditoriums")
    public ResponseEntity<?> createAuditorium(@PathVariable Long CinemaId, @RequestBody AuditoriumDTO body) {
        try {
            auditoriumService.createAuditorium(body, CinemaId);
            return ResponseEntity.status(201).body("Create");
        } catch (UsernameNotFoundException e) {
            return ResponseEntity.status(404).body(e.getMessage());
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(e.getMessage());
        }
    }

    @GetMapping("")
    public ResponseEntity<?> getAllCinemas() {
        try {
            return ResponseEntity.status(200).body(service.getAllCinemas());
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(e.getMessage());
        }
    }

    @GetMapping("/{id}")
    public ResponseEntity<?> getCinemaById(@PathVariable Long id) {
        try {
            CinemaResponse response = service.getCinema(id);
            return ResponseEntity.status(200).body(response);
        } catch (UsernameNotFoundException e) {
            return ResponseEntity.status(404).body(e.getMessage());
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(e.getMessage());
        }
    }

    @GetMapping(params = "city")
    public ResponseEntity<?> getCinemasByCity(@RequestParam String city) {
        try {
            return ResponseEntity.status(200).body(service.getCinemasByCity(city));
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(e.getMessage());
        }
    }
}
