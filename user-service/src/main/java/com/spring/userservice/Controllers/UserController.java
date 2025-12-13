package com.spring.userservice.Controllers;

import com.spring.userservice.DTOs.ChangePasswordForm;
import com.spring.userservice.DTOs.UserDTO;
import com.spring.userservice.Exceptions.ActionNotAllowedException;
import com.spring.userservice.Exceptions.InvalidCredentialsException;
import com.spring.userservice.Exceptions.UserAlreadyExistedException;
import com.spring.userservice.Services.UserService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.PathVariable;
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
    @PreAuthorize("hasAnyAuthority('USER', 'LOCAL_ADMIN', 'SUPER_ADMIN')")
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
    public ResponseEntity<?> getUserProfile(@PathVariable("userId") Long userId) {
        try {
            return ResponseEntity.ok(service.getUserProfile(userId));
        } catch (UsernameNotFoundException e) {
            return ResponseEntity.status(404).body(e.getMessage());
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(e.getMessage());
        }
    }

    @PutMapping("/profile")
    @PreAuthorize("hasAnyAuthority('USER', 'LOCAL_ADMIN', 'SUPER_ADMIN')")
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
    @PreAuthorize("hasAnyAuthority('USER', 'LOCAL_ADMIN', 'SUPER_ADMIN')")
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
    @PreAuthorize("hasAnyAuthority('USER', 'LOCAL_ADMIN', 'SUPER_ADMIN')")
    public ResponseEntity<?> getBookingHistory() {
        try {
            return ResponseEntity.ok(service.bookingHistory());
        } catch (UsernameNotFoundException e) {
            return ResponseEntity.status(404).body(e.getMessage());
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(e.getMessage());
        }
    }

    @PreAuthorize("hasAuthority('LOCAL_ADMIN')")
    @GetMapping("")
    public ResponseEntity<?> getAllUsers() {
        try {
            return ResponseEntity.ok(service.getAllUsers());
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(e.getMessage());
        }
    }

    @PreAuthorize("hasAuthority('LOCAL_ADMIN')")
    @DeleteMapping("/{userId}")
    public ResponseEntity<?> deleteUser(@PathVariable("userId") Long userId) {
        try {
            service.deleteUser(userId);
            return ResponseEntity.ok("User deleted successfully");
        } catch (UsernameNotFoundException e) {
            return ResponseEntity.status(404).body(e.getMessage());
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(e.getMessage());
        }
    }

    @PreAuthorize("hasAuthority('LOCAL_ADMIN')")
    @PutMapping("/{userId}/role")
    public ResponseEntity<?> changeUserRole(@PathVariable("userId") Long userId, @RequestBody String role) {
        try {
            service.changeRoleUser(userId, role);
            return ResponseEntity.ok("User role changed successfully");
        } catch (UsernameNotFoundException e) {
            return ResponseEntity.status(404).body(e.getMessage());
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(e.getMessage());
        }
    }
}
