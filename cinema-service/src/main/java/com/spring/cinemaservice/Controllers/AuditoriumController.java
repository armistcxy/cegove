package com.spring.cinemaservice.Controllers;

import com.spring.cinemaservice.Services.AuditoriumService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
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

    @PreAuthorize("hasAuthority('LOCAL_ADMIN')")
    @PutMapping("/{id}/pattern")
    public ResponseEntity<?> updateAuditorium(@PathVariable("id") Long auditoriumId, @RequestBody String newPattern) {
        try {
            service.updateAuditoriumPattern(auditoriumId, newPattern);
            return ResponseEntity.status(200).body("Auditorium pattern updated successfully");
        } catch (UsernameNotFoundException e) {
            return ResponseEntity.status(404).body(e.getMessage());
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(e.getMessage());
        }
    }

    @PreAuthorize("hasAuthority('LOCAL_ADMIN')")
    @DeleteMapping("/{id}")
    public ResponseEntity<?> deleteAuditorium(@PathVariable("id") Long auditoriumId) {
        try {
            service.deleteAuditorium(auditoriumId);
            return ResponseEntity.status(200).body("Auditorium deleted successfully");
        } catch (UsernameNotFoundException e) {
            return ResponseEntity.status(404).body(e.getMessage());
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(e.getMessage());
        }
    }
}
