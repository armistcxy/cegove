package com.spring.userservice.DTOs;

import com.spring.userservice.Enums.Gender;
import com.spring.userservice.Enums.UserRole;
import lombok.Builder;
import lombok.Data;
import org.springframework.web.multipart.MultipartFile;

import java.time.LocalDate;
import java.time.LocalDateTime;

@Data
@Builder
public class UserDTO {
    private Long id;
    private String fullName;
    private String email;
    private String phone;
    private UserRole role;
    private LocalDate dob;
    private Gender gender;
    private String address;
    private String district;
    private String city;

    private MultipartFile imgFile;
    private String img;

    private LocalDateTime createdAt;
}
