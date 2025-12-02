package com.spring.userservice.Controllers;

import com.spring.userservice.DTOs.ChangePasswordForm;
import com.spring.userservice.DTOs.UserDTO;
import com.spring.userservice.Exceptions.ActionNotAllowedException;
import com.spring.userservice.Exceptions.InvalidCredentialsException;
import com.spring.userservice.Exceptions.UserAlreadyExistedException;
import com.spring.userservice.Services.UserService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.reactive.function.client.WebClientResponseException;

@RestController
@RequestMapping("/users")
public class UserController {
    @Autowired
    private UserService service;

    @GetMapping("/profile")
    public ResponseEntity<?> getProfile() {
        try {
            return ResponseEntity.ok(service.profile());
        } catch (UsernameNotFoundException e) {
            return ResponseEntity.status(404).body(e.getMessage());
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(e.getMessage());
        }
    }

    @GetMapping("/{userId}/profile")
    public ResponseEntity<?> getUserProfile(@ModelAttribute("userId") Long userId) {
        try {
            return ResponseEntity.ok(service.getUserProfile(userId));
        } catch (UsernameNotFoundException e) {
            return ResponseEntity.status(404).body(e.getMessage());
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(e.getMessage());
        }
    }

    @PutMapping("/profile")
    public ResponseEntity<?> updateProfile(@ModelAttribute UserDTO userDTO) {
        try {
            service.updateProfile(userDTO);
            return ResponseEntity.ok("Profile updated successfully");
        } catch (UsernameNotFoundException e) {
            return ResponseEntity.status(404).body(e.getMessage());
        } catch (ActionNotAllowedException e) {
            return ResponseEntity.status(403).body(e.getMessage());
        } catch (UserAlreadyExistedException e) {
            return ResponseEntity.status(409).body(e.getMessage());
        } catch (WebClientResponseException e) {
            return ResponseEntity.status(e.getRawStatusCode()).body(e.getResponseBodyAsString());
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(e.getMessage());
        }
    }

    @PutMapping("/password")
    public ResponseEntity<?> changePassword(@RequestBody ChangePasswordForm form) {
        try {
            service.changePassword(form);
            return ResponseEntity.ok("Password changed successfully");
        } catch (UsernameNotFoundException e) {
            return ResponseEntity.status(404).body(e.getMessage());
        } catch (ActionNotAllowedException e) {
            return ResponseEntity.status(403).body(e.getMessage());
        } catch (InvalidCredentialsException e) {
            return ResponseEntity.status(401).body(e.getMessage());
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(e.getMessage());
        }
    }

    @GetMapping("/booking-history")
    public ResponseEntity<?> getBookingHistory() {
        try {
            return ResponseEntity.ok(service.bookingHistory());
        } catch (UsernameNotFoundException e) {
            return ResponseEntity.status(404).body(e.getMessage());
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(e.getMessage());
        }
    }
}
