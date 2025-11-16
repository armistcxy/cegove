package com.spring.authservice.DTOs;

import com.spring.authservice.Enums.Gender;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.web.multipart.MultipartFile;

import java.time.LocalDate;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class RegisterRequest {
    private String fullName;
    private String email;
    private String phone;
    private String password;

    private LocalDate dob;
    private Gender gender;
    private String address;
    private String district;
    private String city;
    private MultipartFile img;
}
