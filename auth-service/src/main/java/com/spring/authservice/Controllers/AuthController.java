package com.spring.authservice.Controllers;

import com.spring.authservice.DTOs.ChangeForgotPasswordRequest;
import com.spring.authservice.DTOs.LoginRequest;
import com.spring.authservice.DTOs.RegisterRequest;
import com.spring.authservice.DTOs.VerifyOtpRequest;
import com.spring.authservice.Exceptions.InvalidCredentialsException;
import com.spring.authservice.Exceptions.NotAuthorizeException;
import com.spring.authservice.Exceptions.UserAlreadyExistedException;
import com.spring.authservice.Services.AuthService;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/auth")
public class AuthController {
    @Autowired
    private AuthService service;

    @PostMapping("/register")
    public ResponseEntity<?> register(@ModelAttribute RegisterRequest request) {
        try {
            service.register(request);
            return ResponseEntity.ok("User registered successfully");
        } catch (UserAlreadyExistedException e) {
            return ResponseEntity.status(409).body(e.getMessage());
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(e.getMessage());
        }
    }

    @PostMapping("/login")
    public ResponseEntity<?> login(@RequestBody LoginRequest loginForm, HttpServletResponse response) {
        try {
            String token = service.login(loginForm);

            return ResponseEntity.ok(token);
        } catch (UsernameNotFoundException e) {
            return ResponseEntity.status(404).body(e.getMessage());
        } catch (NotAuthorizeException e) {
            return ResponseEntity.status(403).body(e.getMessage());
        } catch (InvalidCredentialsException e) {
            return ResponseEntity.status(401).body(e.getMessage());
        }catch (Exception e) {
            return ResponseEntity.badRequest().body(e.getMessage());
        }
    }

    @PostMapping("/logout")
    public ResponseEntity<?> logout(HttpServletRequest request) {
        try {
            // Get token from header Authorization
            String header = request.getHeader("Authorization");
            String token = null;

            if (header != null && header.startsWith("Bearer ")) {
                token = header.substring(7);
            }

            if (token == null) {
                return ResponseEntity.badRequest().body("No Bearer token found");
            }

            service.logout(token);

            return ResponseEntity.ok("Logout successfully");
        } catch (Exception e) {
            return ResponseEntity.status(500).body("Logout failed: " + e.getMessage());
        }
    }

    @PostMapping("/otp-verify")
    public ResponseEntity<?> verifyOtp(@RequestBody VerifyOtpRequest request) {
        try {
            return ResponseEntity.ok(service.verifyOtp(request));
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(e.getMessage());
        }
    }

    @PostMapping("/forgot-password-change")
    public ResponseEntity<?> changeForgotPassword(@RequestBody ChangeForgotPasswordRequest request) {
        try {
            service.changeForgotPassword(request);
            return ResponseEntity.ok("Password changed successfully");
        } catch (InvalidCredentialsException e) {
            return ResponseEntity.status(401).body(e.getMessage());
        } catch (UsernameNotFoundException e) {
            return ResponseEntity.status(404).body(e.getMessage());
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(e.getMessage());
        }
    }
}
