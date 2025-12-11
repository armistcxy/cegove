package com.spring.cinemaservice.Controllers;

import com.spring.cinemaservice.Services.AuditoriumService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/auditoriums")
public class AuditoriumController {
    @Autowired
    private AuditoriumService service;

    @GetMapping("/{id}")
    public ResponseEntity<?> getAuditoriumById(@PathVariable("id") Long auditoriumId) {
        try {
            return ResponseEntity.status(200).body(service.getAuditoriumById(auditoriumId));
        } catch (UsernameNotFoundException e) {
            return ResponseEntity.status(404).body(e.getMessage());
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(e.getMessage());
        }
    }

}
